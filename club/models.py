from django.db import models
from django.utils import timezone
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField
from wagtail.images import get_image_model_string
from wagtail.models import Page
from wagtail.snippets.models import register_snippet


@register_snippet
class Player(models.Model):
    class Position(models.TextChoices):
        GOALKEEPER = "GK", "Bramkarz"
        DEFENDER = "DF", "Obrońca"
        MIDFIELDER = "MF", "Pomocnik"
        FORWARD = "FW", "Napastnik"

    first_name = models.CharField("imię", max_length=80)
    last_name = models.CharField("nazwisko", max_length=100)
    position = models.CharField("pozycja", max_length=2, choices=Position.choices)
    shirt_number = models.PositiveSmallIntegerField("numer", blank=True, null=True)
    photo = models.ForeignKey(
        get_image_model_string(),
        verbose_name="zdjęcie",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    sort_order = models.PositiveSmallIntegerField("kolejność", default=0)
    is_active = models.BooleanField("w aktualnym składzie", default=True)

    panels = [
        FieldPanel("first_name"),
        FieldPanel("last_name"),
        FieldPanel("position"),
        FieldPanel("shirt_number"),
        FieldPanel("photo"),
        FieldPanel("sort_order"),
        FieldPanel("is_active"),
    ]

    class Meta:
        ordering = ("sort_order", "last_name", "first_name")
        verbose_name = "zawodnik"
        verbose_name_plural = "zawodnicy"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


@register_snippet
class Fixture(models.Model):
    opponent = models.CharField("przeciwnik", max_length=120)
    competition = models.CharField("rozgrywki", max_length=120, blank=True)
    kickoff_at = models.DateTimeField("data i godzina")
    is_home = models.BooleanField("mecz u siebie", default=True)
    venue = models.CharField("miejsce", max_length=160, blank=True)
    home_score = models.PositiveSmallIntegerField("bramki KS Milan", blank=True, null=True)
    away_score = models.PositiveSmallIntegerField("bramki przeciwnika", blank=True, null=True)
    source_name = models.CharField("źródło danych", max_length=100, blank=True)
    updated_at = models.DateTimeField("zaktualizowano", auto_now=True)

    panels = [
        FieldPanel("opponent"),
        FieldPanel("competition"),
        FieldPanel("kickoff_at"),
        FieldPanel("is_home"),
        FieldPanel("venue"),
        FieldPanel("home_score"),
        FieldPanel("away_score"),
        FieldPanel("source_name"),
    ]

    class Meta:
        ordering = ("kickoff_at",)
        verbose_name = "mecz"
        verbose_name_plural = "terminarz i wyniki"

    def __str__(self):
        return f"KS Milan — {self.opponent} ({self.kickoff_at:%d.%m.%Y})"

    @property
    def has_result(self):
        return self.home_score is not None and self.away_score is not None

    @property
    def club_score(self):
        return self.home_score if self.is_home else self.away_score

    @property
    def opponent_score(self):
        return self.away_score if self.is_home else self.home_score


class HomePage(Page):
    hero_eyebrow = models.CharField("nadtytuł", max_length=80, default="KS MILAN · MILANÓWEK")
    hero_heading = models.CharField("nagłówek strony głównej", max_length=120, default="Gramy razem.")
    hero_text = models.CharField(
        "opis strony głównej",
        max_length=240,
        default="Lokalny klub. Wspólna pasja. Piłka, która łączy pokolenia.",
    )

    subpage_types = [
        "club.HistoryPage",
        "club.RosterPage",
        "club.FixturesPage",
        "club.NewsIndexPage",
    ]
    content_panels = Page.content_panels + [
        FieldPanel("hero_eyebrow"),
        FieldPanel("hero_heading"),
        FieldPanel("hero_text"),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        now = timezone.now()
        context["featured_fixture"] = (
            Fixture.objects.filter(kickoff_at__gte=now).order_by("kickoff_at").first()
        )
        context["recent_results"] = Fixture.objects.filter(
            kickoff_at__lt=now,
            home_score__isnull=False,
            away_score__isnull=False,
        ).order_by("-kickoff_at")[:3]
        context["players"] = Player.objects.filter(is_active=True)[:4]
        context["news"] = NewsPage.objects.live().order_by("-first_published_at")[:3]
        return context


class HistoryPage(Page):
    introduction = RichTextField("wprowadzenie", blank=True)
    story = RichTextField("historia klubu", blank=True)

    parent_page_types = ["club.HomePage"]
    subpage_types = []
    content_panels = Page.content_panels + [
        FieldPanel("introduction"),
        FieldPanel("story"),
    ]


class RosterPage(Page):
    introduction = RichTextField("wprowadzenie", blank=True)

    parent_page_types = ["club.HomePage"]
    subpage_types = []
    content_panels = Page.content_panels + [FieldPanel("introduction")]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["players"] = Player.objects.filter(is_active=True)
        return context


class FixturesPage(Page):
    introduction = RichTextField("wprowadzenie", blank=True)

    parent_page_types = ["club.HomePage"]
    subpage_types = []
    content_panels = Page.content_panels + [FieldPanel("introduction")]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["upcoming_fixtures"] = Fixture.objects.filter(
            kickoff_at__gte=timezone.now()
        ).order_by("kickoff_at")
        context["past_fixtures"] = Fixture.objects.filter(
            kickoff_at__lt=timezone.now(),
            home_score__isnull=False,
            away_score__isnull=False,
        ).order_by("-kickoff_at")
        return context


class NewsIndexPage(Page):
    introduction = RichTextField("wprowadzenie", blank=True)

    parent_page_types = ["club.HomePage"]
    subpage_types = ["club.NewsPage"]
    content_panels = Page.content_panels + [FieldPanel("introduction")]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        context["news"] = NewsPage.objects.child_of(self).live().order_by(
            "-first_published_at"
        )
        return context


class NewsPage(Page):
    publication_date = models.DateField("data publikacji", default=timezone.localdate)
    excerpt = models.CharField("krótki opis", max_length=240)
    cover_image = models.ForeignKey(
        get_image_model_string(),
        verbose_name="zdjęcie główne",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    body = RichTextField("treść wpisu")

    parent_page_types = ["club.NewsIndexPage"]
    subpage_types = []
    content_panels = Page.content_panels + [
        FieldPanel("publication_date"),
        FieldPanel("excerpt"),
        FieldPanel("cover_image"),
        FieldPanel("body"),
    ]

    class Meta:
        verbose_name = "aktualność"
        verbose_name_plural = "aktualności"
