"""App-config handlers for `cookie_admin`: reset, api key, prompts.

Split out of `cookie_admin.py` to stay under the 500-line quality gate.
Methods assume `self` is a `Command` instance — see main module for the
shared helpers (`self._error`, `self._success`).
"""

from __future__ import annotations

import json
import logging
import pwd

from django.conf import settings

security_logger = logging.getLogger("security")


class AppConfigMixin:
    """reset + Anthropic/prompts subcommand handlers."""

    # ------------------------------------------------------------------ #
    # reset                                                               #
    # ------------------------------------------------------------------ #

    def _handle_reset(self, options):
        from apps.core import factory_reset

        if options.get("as_json"):
            if not options.get("confirm"):
                self._error(
                    "--confirm flag required for non-interactive reset. Usage: cookie_admin reset --json --confirm",
                    options,
                )
        else:
            self.stderr.write("WARNING: This will permanently delete ALL data.")
            confirm = input("Type RESET to confirm: ")
            if confirm != "RESET":
                self._error("Aborted.", options)

        security_logger.warning("DATABASE RESET initiated via CLI (cookie_admin reset)")

        # This command runs as root via docker exec; recreate media dirs owned by the app user.
        try:
            app_pw = pwd.getpwnam("app")
            owner = (app_pw.pw_uid, app_pw.pw_gid)
        except KeyError:
            owner = None
        actions = factory_reset.reset_all(
            include_accounts=settings.AUTH_MODE == "passkey",
            media_owner=owner,
        )

        security_logger.warning("DATABASE RESET completed successfully via CLI")

        self._success(
            "Database reset complete.",
            options,
            {"actions_performed": actions},
        )

    # ------------------------------------------------------------------ #
    # api key + default model                                             #
    # ------------------------------------------------------------------ #

    def _read_key(self, options):
        """Return a non-empty API key read from --key or stdin. Errors on empty."""
        import sys

        if options.get("stdin"):
            value = sys.stdin.read().strip()
        else:
            value = (options.get("key") or "").strip()
        if not value:
            self._error("API key must be a non-empty value.", options, code=2)
        return value

    def _handle_set_api_key(self, options):
        from apps.core.models import AppSettings

        value = self._read_key(options)
        app = AppSettings.get()
        app.anthropic_api_key = value
        app.save()
        security_logger.warning("cookie_admin set-api-key: key changed")
        self._success("API key saved.", options, {"saved": True})

    def _handle_test_api_key(self, options):
        from apps.ai.services.anthropic_client import AnthropicService

        value = self._read_key(options)
        try:
            ok, reason = AnthropicService.test_connection(value)
        except Exception as exc:
            ok, reason = False, str(exc)
        if options.get("as_json"):
            self.stdout.write(json.dumps({"ok": True, "valid": ok, "reason": reason}))
        else:
            self.stdout.write("valid" if ok else f"invalid: {reason}")
        if not ok:
            raise SystemExit(1)

    def _handle_set_default_model(self, options):
        from apps.ai.models import AIPrompt
        from apps.core.models import AppSettings

        model_id = options["model_id"]
        valid = {m[0] for m in AIPrompt.AVAILABLE_MODELS}
        if model_id not in valid:
            self._error(
                f"Unknown model '{model_id}'. Valid: {sorted(valid)}",
                options,
                code=2,
            )
        app = AppSettings.get()
        app.default_ai_model = model_id
        app.save()
        security_logger.warning("cookie_admin set-default-model: %s", model_id)
        self._success(f"Default model set to {model_id}.", options, {"default_ai_model": model_id})

    # ------------------------------------------------------------------ #
    # prompts                                                             #
    # ------------------------------------------------------------------ #

    def _handle_prompts_list(self, options):
        from apps.ai.models import AIPrompt

        rows = list(AIPrompt.objects.order_by("prompt_type").values("prompt_type", "name", "model", "is_active"))
        if options.get("as_json"):
            self.stdout.write(json.dumps({"ok": True, "prompts": rows}))
            return
        for r in rows:
            self.stdout.write(
                f"{r['prompt_type']:<22} model={r['model']:<35} active={r['is_active']}  name={r['name']!r}"
            )

    def _handle_prompts_show(self, options):
        from apps.ai.models import AIPrompt

        try:
            p = AIPrompt.objects.get(prompt_type=options["prompt_type"])
        except AIPrompt.DoesNotExist:
            self._error(f"Prompt '{options['prompt_type']}' not found.", options, code=2)
        payload = {
            "prompt_type": p.prompt_type,
            "name": p.name,
            "description": p.description,
            "model": p.model,
            "is_active": p.is_active,
            "system_prompt": p.system_prompt,
            "user_prompt_template": p.user_prompt_template,
        }
        if options.get("as_json"):
            self.stdout.write(json.dumps({"ok": True, "prompt": payload}))
            return
        self.stdout.write(f"prompt_type: {p.prompt_type}")
        self.stdout.write(f"name:        {p.name}")
        self.stdout.write(f"description: {p.description}")
        self.stdout.write(f"model:       {p.model}")
        self.stdout.write(f"is_active:   {p.is_active}")
        self.stdout.write("system_prompt:")
        self.stdout.write(p.system_prompt)
        self.stdout.write("user_prompt_template:")
        self.stdout.write(p.user_prompt_template)

    def _handle_prompts_set(self, options):
        from apps.ai.models import AIPrompt

        prompt_type = options["prompt_type"]
        try:
            prompt = AIPrompt.objects.get(prompt_type=prompt_type)
        except AIPrompt.DoesNotExist:
            self._error(f"Prompt '{prompt_type}' not found.", options, code=2)

        # Read files FIRST (before any DB write) so a missing file doesn't leave
        # a half-updated row.
        updated_fields = []
        new_system = new_user = None
        if options.get("system_file"):
            new_system = self._read_text_file(options["system_file"], options)
            updated_fields.append("system_prompt")
        if options.get("user_file"):
            new_user = self._read_text_file(options["user_file"], options)
            updated_fields.append("user_prompt_template")
        if options.get("model"):
            valid = {m[0] for m in AIPrompt.AVAILABLE_MODELS}
            if options["model"] not in valid:
                self._error(
                    f"Unknown model '{options['model']}'. Valid: {sorted(valid)}",
                    options,
                    code=2,
                )
            updated_fields.append("model")
        if options.get("active"):
            updated_fields.append("is_active")
        if not updated_fields:
            self._error(
                "prompts set: specify at least one of --system-file, --user-file, --model, --active.", options, code=2
            )

        if new_system is not None:
            prompt.system_prompt = new_system
        if new_user is not None:
            prompt.user_prompt_template = new_user
        if options.get("model"):
            prompt.model = options["model"]
        if options.get("active"):
            prompt.is_active = options["active"] == "true"
        prompt.save()

        security_logger.warning("cookie_admin prompts set %s: fields=%s", prompt_type, updated_fields)
        self._success(
            f"Prompt {prompt_type} updated: fields={updated_fields}",
            options,
            {"prompt_type": prompt_type, "updated_fields": updated_fields},
        )

    def _read_text_file(self, path, options):
        try:
            with open(path, encoding="utf-8") as fh:
                return fh.read()
        except (OSError, UnicodeDecodeError) as exc:
            self._error(f"Cannot read file '{path}': {exc}", options, code=2)
