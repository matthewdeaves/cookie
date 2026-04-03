"""Override Django's createsuperuser to block usage.

This project uses passkey authentication with cookie_admin for user management.
Django superusers serve no purpose — there is no /admin/ URL.

To create an admin:
    1. Register via passkey flow
    2. Promote with: manage.py cookie_admin promote <username>
"""

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Blocked — use cookie_admin promote instead."

    def handle(self, *args, **options):
        raise CommandError(
            "createsuperuser is disabled. This project uses passkey auth.\n"
            "Register via the passkey flow, then promote with:\n"
            "  manage.py cookie_admin promote <username>"
        )
