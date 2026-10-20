from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from wagtail.models import Page, Site

from .models import (
    Fixture,
    FixturesPage,
    HomePage,
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
