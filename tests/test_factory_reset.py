"""Tests for apps.core.factory_reset: the interface is the test surface."""

from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache

from apps.core import factory_reset
from apps.core.models import DeviceCode
from apps.profiles.models import Profile
from apps.recipes.models import Recipe, RecipeFavorite, SearchSource


@pytest.fixture
def media(tmp_path):
    for sub in factory_reset.MEDIA_SUBDIRS:
        (tmp_path / sub).mkdir()
        (tmp_path / sub / "x.jpg").write_bytes(b"x")
    (tmp_path / "keep.txt").write_text("keep")
    return tmp_path


@pytest.fixture
def populated(db):
    profile = Profile.objects.create(name="P", avatar_color="#fff")
    recipe = Recipe.objects.create(profile=profile, title="R", host="h", ingredients=["a"], instructions=["b"])
    RecipeFavorite.objects.create(profile=profile, recipe=recipe)
    return profile


@pytest.mark.django_db
class TestPreview:
    def test_counts_cover_every_reset_table(self, populated):
        counts = factory_reset.preview_counts()
        assert set(counts) == {key for key, _ in factory_reset.RESET_TABLES} | {"recipe_images"}
        assert counts["profiles"] == 1
        assert counts["recipes"] == 1
        assert counts["favorites"] == 1
        assert counts["recipe_images"] == 0


@pytest.mark.django_db
class TestResetAll:
    @patch("apps.core.factory_reset.call_command")
    def test_wipes_data_media_cache_and_sessions(self, mock_cmd, populated, media):
        from django.contrib.sessions.backends.db import SessionStore
        from django.contrib.sessions.models import Session

        cache.set("k", "v")
        s = SessionStore()
        s["a"] = 1
        s.create()

        actions = factory_reset.reset_all(media_root=str(media))

        assert Profile.objects.count() == 0
        assert Recipe.objects.count() == 0
        assert cache.get("k") is None
        assert Session.objects.count() == 0
        for sub in factory_reset.MEDIA_SUBDIRS:
            assert list((media / sub).iterdir()) == []
        assert (media / "keep.txt").exists()
        assert "Cleared application cache" in actions
        assert "Seeded search_sources" in actions
        assert [c.args[0] for c in mock_cmd.call_args_list] == ["migrate", *factory_reset.SEED_COMMANDS]

    @patch("apps.core.factory_reset.call_command")
    def test_missing_media_dirs_are_created(self, mock_cmd, db, tmp_path):
        factory_reset.reset_all(media_root=str(tmp_path))
        for sub in factory_reset.MEDIA_SUBDIRS:
            assert (tmp_path / sub).is_dir()

    @patch("apps.core.factory_reset.call_command")
    def test_resets_source_counters_but_keeps_sources(self, mock_cmd, db, tmp_path):
        src = SearchSource.objects.create(
            host="t.example.com",
            name="T",
            search_url_template="https://t.example.com/?q={query}",
            result_selector=".r",
            consecutive_failures=5,
            needs_attention=True,
        )
        factory_reset.reset_all(media_root=str(tmp_path))
        src.refresh_from_db()
        assert (src.consecutive_failures, src.needs_attention) == (0, False)

    @patch("apps.core.factory_reset.call_command")
    def test_accounts_kept_unless_requested(self, mock_cmd, db, tmp_path):
        User.objects.create_user(username="pk_a")
        factory_reset.reset_all(media_root=str(tmp_path))
        assert User.objects.filter(username="pk_a").exists()

        DeviceCode.objects.all().delete()
        factory_reset.reset_all(media_root=str(tmp_path), include_accounts=True)
        assert User.objects.count() == 0

    def test_failing_seed_is_skipped_not_fatal(self, db, tmp_path):
        def fake(cmd, **kw):
            if cmd == "seed_ai_prompts":
                raise RuntimeError("nope")

        with patch("apps.core.factory_reset.call_command", side_effect=fake):
            actions = factory_reset.reset_all(media_root=str(tmp_path))
        assert "Seeded search_sources" in actions
        assert "Seeded ai_prompts" not in actions

    @patch("apps.core.factory_reset.os.chown")
    @patch("apps.core.factory_reset.call_command")
    def test_media_owner_is_applied(self, mock_cmd, mock_chown, db, tmp_path):
        factory_reset.reset_all(media_root=str(tmp_path), media_owner=(1, 2))
        assert mock_chown.call_count == len(factory_reset.MEDIA_SUBDIRS)
        assert mock_chown.call_args.args[1:] == (1, 2)
