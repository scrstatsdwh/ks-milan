from datetime import timedelta
from io import StringIO
import os
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from wagtail.models import Page, Site

from .models import (
    Fixture,
    FixturesPage,
    HomePage,
    HistoryPage,
    NewsIndexPage,
    NewsPage,
    Player,
    RosterPage,
)


class ClubPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.home = HomePage(title="KS Milan", slug="ks-milan")
        Page.get_first_root_node().add_child(instance=cls.home)
        cls.home.save_revision().publish()
        Site.objects.update_or_create(
            hostname="testserver",
            defaults={"port": 80, "root_page": cls.home, "is_default_site": True},
        )

    def test_homepage_renders_club_sections(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "KS Milan")
        self.assertContains(response, "Skład")
        self.assertContains(response, "club/images/milan.svg")

    def test_wagtail_editor_login_is_available(self):
        response = self.client.get("/cms/login/")

        self.assertEqual(response.status_code, 200)

    def test_history_motto_keeps_accessible_text_and_animated_letters(self):
        history_page = self.home.add_child(
            instance=HistoryPage(
                title="Historia",
                slug="historia",
                story="<p>Pełna notatka historyczna.</p>",
            )
        )
        history_page.save_revision().publish()

        response = self.client.get("/historia/")

        self.assertContains(
            response,
            '<span class="visually-hidden">Klub. Miasto. Wspólna pasja.</span>',
            html=True,
        )
        self.assertContains(response, 'class="article-aside__letter"')
        self.assertContains(response, 'aria-label="Historia KS Milan w porządku chronologicznym"')
        self.assertContains(response, "Sezon 1992/93")
        self.assertContains(response, "Grudzień 2009")
        self.assertContains(response, 'class="history-timeline__card"')
        self.assertContains(response, "is-active is-passed")
        self.assertContains(response, 'club/images/milan-timeline-ball.svg')
        self.assertNotContains(response, '<img src="/static/club/images/milan.svg" alt="">')
        self.assertContains(response, "Przeczytaj pełny opis historii")
        self.assertContains(response, "Pełna notatka historyczna.")
        self.assertEqual(response.content.count(b'data-timeline-event>'), 14)

    def test_roster_page_lists_active_players(self):
        roster_page = self.home.add_child(
            instance=RosterPage(title="Skład", slug="sklad")
        )
        roster_page.save_revision().publish()
        Player.objects.create(first_name="Jan", last_name="Kowalski", position="GK")
        Player.objects.create(
            first_name="Adam", last_name="Nowak", position="DF", is_active=False
        )

        response = self.client.get("/sklad/")

        self.assertContains(response, "Jan")
        self.assertContains(response, "Kowalski")
        self.assertNotContains(response, "Adam Nowak")

    def test_upcoming_fixture_is_shown_on_homepage(self):
        Fixture.objects.create(
            opponent="Goście FC",
            competition="Liga",
            kickoff_at=timezone.now() + timedelta(days=2),
            is_home=True,
        )

        response = self.client.get("/")

        self.assertContains(response, "Goście FC")

    def test_away_result_is_displayed_from_the_opponents_perspective(self):
        fixtures_page = self.home.add_child(
            instance=FixturesPage(title="Terminarz", slug="terminarz")
        )
        fixtures_page.save_revision().publish()
        Fixture.objects.create(
            opponent="Rywale FC",
            competition="Liga",
            kickoff_at=timezone.now() - timedelta(days=2),
            is_home=False,
            home_score=3,
            away_score=1,
        )

        response = self.client.get("/terminarz/")

        self.assertContains(response, "Rywale FC")
        self.assertContains(response, "1 : 3")

    def test_published_news_is_visible_on_its_detail_page(self):
        news_index = self.home.add_child(
            instance=NewsIndexPage(title="Aktualności", slug="aktualnosci")
        )
        news_index.save_revision().publish()
        article = news_index.add_child(
            instance=NewsPage(
                title="Klubowy trening",
                slug="klubowy-trening",
                excerpt="Trenujemy razem.",
                body="<p>Do zobaczenia na boisku.</p>",
            )
        )
        article.save_revision().publish()

        response = self.client.get("/aktualnosci/klubowy-trening/")

        self.assertContains(response, "Klubowy trening")
        self.assertContains(response, "Do zobaczenia na boisku.")


class BootstrapCommandTests(TestCase):
    def test_bootstrap_site_creates_homepage_and_default_site_idempotently(self):
        output = StringIO()
        Site.objects.all().delete()

        call_command("bootstrap_site", stdout=output)
        call_command("bootstrap_site", stdout=output)

        root = Page.get_first_root_node()
        homepage = HomePage.objects.get(slug="ks-milan", path__startswith=root.path)
        site = Site.objects.get(is_default_site=True)
        self.assertTrue(homepage.live)
        self.assertEqual(site.root_page_id, homepage.pk)
        self.assertEqual(HomePage.objects.filter(slug="ks-milan").count(), 1)


class CreateTestUserCommandTests(TestCase):
    def test_creates_local_superuser_and_is_idempotent(self):
        output = StringIO()

        with override_settings(DEBUG=True), patch.dict(
            os.environ,
            {
                "CREATE_TEST_USER": "false",
                "TEST_CMS_USERNAME": "testadmin",
                "TEST_CMS_EMAIL": "admin@example.com",
                "TEST_CMS_PASSWORD": "Admin123!",
            },
        ):
            call_command("create_test_user", stdout=output)
            user = get_user_model().objects.get(username="testadmin")
            self.assertTrue(user.is_staff)
            self.assertTrue(user.is_superuser)
            self.assertTrue(user.check_password("Admin123!"))
            self.assertIn("testadmin / Admin123!", output.getvalue())
            self.assertTrue(self.client.login(username="testadmin", password="Admin123!"))
            self.assertEqual(self.client.get("/cms/").status_code, 200)

            user.set_password("keep-this-password")
            user.save(update_fields=["password"])
            call_command("create_test_user", stdout=StringIO())
            user.refresh_from_db()
            self.assertTrue(user.check_password("keep-this-password"))

    def test_skips_creation_outside_debug_without_explicit_opt_in(self):
        with (
            override_settings(DEBUG=False),
            patch.dict(os.environ, {"CREATE_TEST_USER": "false"}, clear=False),
        ):
            output = StringIO()
            call_command("create_test_user", stdout=output)

        self.assertFalse(get_user_model().objects.filter(username="admin").exists())
        self.assertIn("skipped", output.getvalue())
        self.assertNotIn("Admin123!", output.getvalue())

    def test_production_opt_in_requires_custom_password_and_never_logs_it(self):
        with (
            override_settings(DEBUG=False),
            patch.dict(
                os.environ,
                {
                    "CREATE_TEST_USER": "true",
                    "TEST_CMS_USERNAME": "testadmin",
                },
                clear=False,
            ),
        ):
            os.environ.pop("TEST_CMS_PASSWORD", None)
            with self.assertRaisesMessage(CommandError, "TEST_CMS_PASSWORD"):
                call_command("create_test_user", stdout=StringIO())

        secret = "unique-production-test-password"
        output = StringIO()
        with (
            override_settings(DEBUG=False),
            patch.dict(
                os.environ,
                {
                    "CREATE_TEST_USER": "true",
                    "TEST_CMS_USERNAME": "testadmin",
                    "TEST_CMS_PASSWORD": secret,
                },
                clear=False,
            ),
        ):
            call_command("create_test_user", stdout=output)

        user = get_user_model().objects.get(username="testadmin")
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password(secret))
        self.assertNotIn(secret, output.getvalue())
        self.assertNotIn("Admin123!", output.getvalue())

    def test_update_existing_only_changes_credentials_when_requested(self):
        user_model = get_user_model()
        user = user_model.objects.create_user(
            username="admin",
            email="old@example.com",
            password="original-password",
        )
        output = StringIO()

        with override_settings(DEBUG=True), patch.dict(
            os.environ,
            {
                "CREATE_TEST_USER": "false",
                "TEST_CMS_EMAIL": "admin@example.com",
                "TEST_CMS_PASSWORD": "Admin123!",
            },
        ):
            call_command("create_test_user", stdout=output)
            user.refresh_from_db()
            self.assertEqual(user.email, "old@example.com")
            self.assertTrue(user.check_password("original-password"))
            self.assertNotIn("Admin123!", output.getvalue())

            call_command("create_test_user", "--update-existing", stdout=StringIO())
            user.refresh_from_db()

        self.assertEqual(user.email, "admin@example.com")
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password("Admin123!"))
