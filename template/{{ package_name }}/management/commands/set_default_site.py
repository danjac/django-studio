from __future__ import annotations

from typing import Any

from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandParser


class Command(BaseCommand):
    """Set the domain and name of the default Django site."""

    help = "Set the domain and name of the default site."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add domain and name positional arguments."""
        parser.add_argument("domain", help="Site domain (e.g. example.com)")
        parser.add_argument("name", help="Human-readable site name")

    def handle(self, *, domain: str, name: str, **options: Any) -> None:
        """Update the current site's domain and name."""
        site = Site.objects.get_current()
        site.domain = domain
        site.name = name
        site.save()
        self.stdout.write(self.style.SUCCESS(f"Default site set to {name} ({domain})"))
