from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand
from wagtail.models import Page, Site

from club.models import (
    Fixture,
    FixturesPage,
    HistoryPage,
    HomePage,
    NewsIndexPage,
    Player,
    RosterPage,
)


class Command(BaseCommand):
    help = "Create the initial KS Milan page tree and local Wagtail site."

    def handle(self, *args, **options):
        root = Page.get_first_root_node()
        homepage = HomePage.objects.child_of(root).first()
        if homepage is None:
            homepage = root.add_child(
                instance=HomePage(
                    title="KS Milan",
                    slug="ks-milan",
                    hero_heading="Gramy razem.",
                )
            )
            homepage.save_revision().publish()
        elif not homepage.live:
            homepage.save_revision().publish()

        default_site = Site.objects.filter(is_default_site=True).first()
        if default_site is None:
            default_site = Site.objects.order_by("pk").first()
        Site.objects.update_or_create(
            hostname=default_site.hostname if default_site else "localhost",
            port=default_site.port if default_site else 8000,
            defaults={
                "root_page": homepage,
                "is_default_site": True,
                "site_name": "KS Milan",
            },
        )

        child_pages = (
            (HistoryPage, "Historia", "historia"),
            (RosterPage, "Skład", "sklad"),
            (FixturesPage, "Terminarz", "terminarz"),
            (NewsIndexPage, "Aktualności", "aktualnosci"),
        )

        for page_type, title, slug in child_pages:
            page = page_type.objects.child_of(homepage).first()
            if page is None:
                page = homepage.add_child(instance=page_type(title=title, slug=slug))
            if not page.live:
                page.save_revision().publish()

        for group_name in ("Editors", "Moderators"):
            group = Group.objects.filter(name=group_name).first()
            if group is None:
                continue
            for model in (Player, Fixture):
                content_type = ContentType.objects.get_for_model(model)
                permissions = Permission.objects.filter(
                    content_type=content_type,
                    codename__in=(
                        f"add_{model._meta.model_name}",
                        f"change_{model._meta.model_name}",
                        f"delete_{model._meta.model_name}",
                        f"view_{model._meta.model_name}",
                    ),
                )
                group.permissions.add(*permissions)

        self.stdout.write(self.style.SUCCESS("KS Milan page tree is ready."))
