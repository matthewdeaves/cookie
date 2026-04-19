"""Resource-oriented handlers for `cookie_admin`: sources, quota, rename.

Split out of `cookie_admin.py` to stay under the 500-line quality gate.
Methods assume `self` is a `Command` instance.
"""

from __future__ import annotations

import json
import logging

from django.conf import settings
from django.contrib.auth.models import User

security_logger = logging.getLogger("security")


class ResourcesMixin:
    """sources, quota, rename subcommand handlers."""

    # ------------------------------------------------------------------ #
    # sources                                                             #
    # ------------------------------------------------------------------ #

    def _handle_sources_list(self, options):
        from apps.recipes.models import SearchSource

        qs = SearchSource.objects.order_by("name")
        if options.get("attention"):
            qs = qs.filter(needs_attention=True)
        rows = [
            {
                "id": s.id,
                "name": s.name,
                "host": s.host,
                "url": s.search_url_template,
                "enabled": s.is_enabled,
                "needs_attention": s.needs_attention,
                "selector": s.result_selector,
            }
            for s in qs
        ]
        if options.get("as_json"):
            self.stdout.write(json.dumps({"ok": True, "sources": rows}))
            return
        for r in rows:
            self.stdout.write(
                f"{r['id']:>3}  enabled={r['enabled']}  attention={r['needs_attention']}  {r['name']}  {r['host']}"
            )

    def _handle_sources_toggle(self, options):
        from apps.recipes.models import SearchSource

        sid = options["source_id"]
        try:
            source = SearchSource.objects.get(id=sid)
        except SearchSource.DoesNotExist:
            self._error(f"Source {sid} not found.", options, code=1)
        source.is_enabled = not source.is_enabled
        source.save(update_fields=["is_enabled"])
        security_logger.warning("cookie_admin sources toggle %d: %s", sid, source.is_enabled)
        self._success(
            f"Source {sid} ({source.name}): enabled={source.is_enabled}",
            options,
            {"source_id": sid, "enabled": source.is_enabled},
        )

    def _handle_sources_toggle_all(self, options):
        from apps.recipes.models import SearchSource

        value = bool(options.get("enable"))
        count = SearchSource.objects.all().update(is_enabled=value)
        security_logger.warning("cookie_admin sources toggle-all: enabled=%s count=%d", value, count)
        self._success(
            f"Set enabled={value} for {count} sources.",
            options,
            {"enabled": value, "count": count},
        )

    def _handle_sources_set_selector(self, options):
        from apps.recipes.models import SearchSource

        sid = options["source_id"]
        selector = options["selector"].strip()
        if not selector:
            self._error("--selector must be a non-empty string.", options, code=2)
        try:
            source = SearchSource.objects.get(id=sid)
        except SearchSource.DoesNotExist:
            self._error(f"Source {sid} not found.", options, code=1)
        source.result_selector = selector
        source.save(update_fields=["result_selector"])
        security_logger.warning("cookie_admin sources set-selector %d", sid)
        self._success(
            f"Source {sid} ({source.name}): selector updated.",
            options,
            {"source_id": sid, "selector": selector},
        )

    def _handle_sources_test(self, options):
        import asyncio

        from apps.recipes.models import SearchSource
        from apps.recipes.services.source_health import check_all_sources, check_source

        if options.get("test_all"):
            results = asyncio.run(check_all_sources())
        else:
            sid = options["source_id"]
            try:
                source = SearchSource.objects.get(id=sid)
            except SearchSource.DoesNotExist:
                self._error(f"Source {sid} not found.", options, code=1)
            results = [asyncio.run(check_source(source))]

        ok_count = sum(1 for r in results if r["ok"])
        fail_count = len(results) - ok_count
        if options.get("as_json"):
            self.stdout.write(
                json.dumps({"ok": True, "results": results, "summary": {"ok": ok_count, "failed": fail_count}})
            )
            return
        for r in results:
            marker = "[OK]  " if r["ok"] else "[FAIL]"
            self.stdout.write(f"{marker} Source {r['source_id']} ({r['name']}) — {r['message']}")
        self.stdout.write(f"{ok_count} ok / {fail_count} failed")

    def _handle_sources_repair(self, options):
        from apps.ai.services.selector import repair_selector
        from apps.core.models import AppSettings
        from apps.recipes.models import SearchSource

        if not AppSettings.get().openrouter_api_key:
            self._error(
                "sources repair requires OPENROUTER_API_KEY or AppSettings.openrouter_api_key to be set.",
                options,
                code=2,
            )
        sid = options["source_id"]
        try:
            source = SearchSource.objects.get(id=sid)
        except SearchSource.DoesNotExist:
            self._error(f"Source {sid} not found.", options, code=1)
        try:
            result = repair_selector(source_id=sid, html_sample=None, auto_update=False)
        except Exception as exc:
            self._error(f"repair failed: {exc}", options, code=1)
        security_logger.warning("cookie_admin sources repair %d", sid)
        self._success(
            f"Source {sid} ({source.name}): selector repaired.",
            options,
            {"source_id": sid, "result": result},
        )

    # ------------------------------------------------------------------ #
    # quota                                                               #
    # ------------------------------------------------------------------ #

    def _handle_quota_show(self, options):
        from apps.core.models import AppSettings

        app = AppSettings.get()
        data = {
            "remix": app.daily_limit_remix,
            "remix_suggestions": app.daily_limit_remix_suggestions,
            "scale": app.daily_limit_scale,
            "tips": app.daily_limit_tips,
            "discover": app.daily_limit_discover,
            "timer": app.daily_limit_timer,
        }
        if options.get("as_json"):
            self.stdout.write(json.dumps({"ok": True, "quotas": data}))
            return
        for name, value in data.items():
            self.stdout.write(f"{name:<18} = {value}")

    def _handle_quota_set(self, options):
        from apps.core.models import AppSettings

        value = options["value"]
        if value < 0:
            self._error("Quota value must be a non-negative integer.", options, code=2)
        feature = options["feature"]
        field = {
            "remix": "daily_limit_remix",
            "remix-suggestions": "daily_limit_remix_suggestions",
            "scale": "daily_limit_scale",
            "tips": "daily_limit_tips",
            "discover": "daily_limit_discover",
            "timer": "daily_limit_timer",
        }[feature]
        app = AppSettings.get()
        setattr(app, field, value)
        app.save()
        security_logger.warning("cookie_admin quota set %s=%d", feature, value)
        self._success(f"quota.{feature} = {value}", options, {feature: value})

    # ------------------------------------------------------------------ #
    # rename                                                              #
    # ------------------------------------------------------------------ #

    def _handle_rename(self, options):
        from apps.profiles.models import Profile

        target = options["target"]
        new_name = (options["name"] or "").strip()
        if not new_name:
            self._error("--name must be a non-empty value.", options, code=2)
        max_len = Profile._meta.get_field("name").max_length
        if len(new_name) > max_len:
            self._error(f"--name exceeds max length {max_len}.", options, code=2)

        if settings.AUTH_MODE == "passkey":
            user = None
            if target.isdigit():
                try:
                    user = User.objects.get(pk=int(target))
                except User.DoesNotExist:
                    pass
            if user is None:
                try:
                    user = User.objects.get(username=target)
                except User.DoesNotExist:
                    self._error(f"No user found for '{target}'.", options, code=1)
            profile = getattr(user, "profile", None)
            if profile is None:
                self._error(f"User '{target}' has no profile.", options, code=1)
        else:
            if not target.isdigit():
                self._error("home mode: positional arg must be a Profile id (integer).", options, code=2)
            try:
                profile = Profile.objects.get(pk=int(target))
            except Profile.DoesNotExist:
                self._error(f"No profile with id {target}.", options, code=1)

        old_name = profile.name
        profile.name = new_name
        profile.save(update_fields=["name"])
        security_logger.warning("cookie_admin rename profile_id=%d: %s → %s", profile.id, old_name, new_name)
        self._success(
            f"Profile renamed: {old_name} → {new_name} (profile_id={profile.id})",
            options,
            {"profile_id": profile.id, "old_name": old_name, "new_name": new_name},
        )
