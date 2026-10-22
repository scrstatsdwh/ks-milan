import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a local test superuser for the Wagtail CMS."

    def add_arguments(self, parser):
        parser.add_argument(
            "--update-existing",
            action="store_true",
            help="Update the existing user's email, permissions, and password.",
        )

    def handle(self, *args, **options):
        create_test_user = os.getenv("CREATE_TEST_USER", "").lower() == "true"
        if not settings.DEBUG and not create_test_user:
            self.stdout.write(
                self.style.WARNING(
                    "Test CMS user creation skipped; enable DJANGO_DEBUG or "
                    "CREATE_TEST_USER=true to opt in."
                )
            )
            return

        username = os.getenv("TEST_CMS_USERNAME", "admin").strip()
        email = os.getenv("TEST_CMS_EMAIL", "admin@example.com").strip()
        password = os.getenv("TEST_CMS_PASSWORD", "Admin123!")
        if not username.strip():
            raise CommandError("TEST_CMS_USERNAME must not be empty.")
        if not password:
            raise CommandError("TEST_CMS_PASSWORD must not be empty.")
        if not settings.DEBUG and not os.getenv("TEST_CMS_PASSWORD"):
            raise CommandError(
                "Set a unique TEST_CMS_PASSWORD before creating a test user "
                "outside debug mode."
            )

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password(password)
            user.save(update_fields=["password"])
        elif options["update_existing"]:
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.set_password(password)
            user.save(
                update_fields=["email", "is_staff", "is_superuser", "password"]
            )

        if settings.DEBUG:
            if created or options["update_existing"]:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Test CMS user {'created' if created else 'updated'}: "
                        f"{username} / {password}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"Test CMS user already exists: {username}; "
                        "use --update-existing to reset its credentials."
                    )
                )
        elif created or options["update_existing"]:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Test CMS user {'created' if created else 'updated'}: {username}"
                )
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"Test CMS user already exists: {username}.")
            )
