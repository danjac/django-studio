import pytest
from django.contrib.sites.models import Site
from django.core.management import call_command


@pytest.mark.django_db
class TestSetDefaultSite:
    def test_sets_domain_and_name(self):
        call_command("set_default_site", "example.com", "My App")
        site = Site.objects.get_current()
        assert site.domain == "example.com"
        assert site.name == "My App"
