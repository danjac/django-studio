# Maps

Free map embedding via [OpenStreetMap](https://www.openstreetmap.org/) and geocoding
via [geopy](https://geopy.readthedocs.io/) (Nominatim). No API key required for either.

## Contents

- [CSP](#csp)
- [Model fields](#model-fields)
- [Geocoding task](#geocoding-task)
- [Triggering geocoding on save](#triggering-geocoding-on-save)
- [Template embed](#template-embed)
- [PostGIS and GeoDjango](#postgis-and-geodjango)

## CSP

Define a maps CSP variant in `config/settings.py` that extends the base policy
with `frame-src` for the OSM iframe:

```python
# config/settings.py
SECURE_CSP_MAPS = {**SECURE_CSP, "frame-src": ["https://www.openstreetmap.org"]}
```

Apply it per-view with `@csp_override` — do not add `frame-src` globally:

```python
from django.conf import settings
from django.views.decorators.csp import csp_override


@csp_override(settings.SECURE_CSP_MAPS)
def venue_detail(request, pk):
    ...
```

## Model fields

Store coordinates as `DecimalField` — `FloatField` loses precision at scale:

```python
from django.db import models

class Venue(models.Model):
    ...
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    def get_osm_embed_url(self, osm_margin: float = 0.1) -> str | None:
        if self.latitude is not None and self.longitude is not None:
            lat, lon = float(self.latitude), float(self.longitude)
            bbox = f"{lon - osm_margin},{lat - osm_margin},{lon + osm_margin},{lat + osm_margin}"
            return (
                f"https://www.openstreetmap.org/export/embed.html"
                f"?bbox={bbox}&layer=mapnik&marker={lat},{lon}"
            )
        return None
```

## Geocoding task

Run geocoding in the background with `django-tasks` so it never blocks a request.
Use `filter().update()` rather than `instance.save()` to avoid re-triggering signals.

```python
import logging

from django.db import models
from django_tasks import task
from geopy.geocoders import Nominatim

logger = logging.getLogger(__name__)


def _geocode(address: str) -> object:
    """Run Nominatim geocoding synchronously."""
    return Nominatim(user_agent="my-project").geocode(address)


@task
def geocode_venue(*, venue_pk: int) -> None:
    """Geocode a venue's address and store the lat/lng coordinates."""
    try:
        venue = Venue.objects.get(pk=venue_pk)
    except Venue.DoesNotExist:
        logger.warning("geocode_venue: venue %d not found", venue_pk)
        return

    address_parts = filter(
        None,
        [
            venue.street_address,
            venue.city,
            venue.region,
            venue.postal_code,
            str(venue.country.name) if venue.country else None,
        ],
    )
    address = ", ".join(address_parts)
    location = _geocode(address)

    if location is None:
        logger.warning("geocode_venue: no result for venue %d (%r)", venue_pk, address)
        return

    Venue.objects.filter(pk=venue_pk).update(
        latitude=location.latitude,  # type: ignore[attr-defined]
        longitude=location.longitude,  # type: ignore[attr-defined]
    )
```

## Triggering geocoding on save

Use a `post_save` signal to enqueue the task whenever the address changes. Check
for coordinate presence to avoid re-geocoding on every save:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Venue)
def enqueue_geocoding(
    sender: type[Venue],
    instance: Venue,
    created: bool,
    update_fields: frozenset[str] | None,
    **kwargs: object,
) -> None:
    address_fields = {"street_address", "city", "region", "postal_code", "country"}
    fields_changed = update_fields is None or bool(address_fields & set(update_fields))
    if fields_changed:
        geocode_venue.enqueue(venue_pk=instance.pk)
```

Connect the signal in `apps.py`:

```python
class VenuesConfig(AppConfig):
    ...
    def ready(self) -> None:
        import venues.signals  # noqa: F401
```

## Template embed

```html+django
{% with osm_embed_url=object.get_osm_embed_url %}
  {% if osm_embed_url %}
  <div>
    <iframe
      src="{{ osm_embed_url }}"
      title="{% translate "Map" %}"
      class="w-full rounded-lg border border-zinc-200 dark:border-zinc-700"
      height="300"
      loading="lazy"
      referrerpolicy="no-referrer"
      sandbox="allow-scripts allow-same-origin"
    ></iframe>
    <p class="mt-1 text-xs text-zinc-500">
      {% blocktranslate trimmed %}
        Map data &copy;
        <a
          href="https://www.openstreetmap.org/copyright"
          class="underline"
          target="_blank"
          rel="noopener noreferrer"
        >OpenStreetMap</a>
        contributors
      {% endblocktranslate %}
    </p>
  </div>
  {% endif %}
{% endwith %}
```

## PostGIS and GeoDjango

The `DecimalField` approach above works for simple "store a point and show it
on a map" use cases. For spatial queries (distance lookups, bounding-box
filters, polygon containment) use PostGIS and Django's built-in
[GeoDjango](https://docs.djangoproject.com/en/stable/ref/contrib/gis/) framework.

### When to upgrade

- Radius searches ("venues within 10 km")
- Ordering by distance from a point
- Storing polygons, lines, or multi-points (delivery zones, routes)
- Spatial joins or intersections between geometries

If you only need to store and display a single lat/lng, `DecimalField` is
simpler — no PostGIS extension required.

### Setup

1. Enable PostGIS via a migration (create an empty migration in your app):

   ```python
   from django.contrib.postgres.operations import CreateExtension
   from django.db import migrations


   class Migration(migrations.Migration):
       dependencies = [...]

       operations = [
           CreateExtension("postgis"),
       ]
   ```

2. Switch the database engine in `config/settings.py`:

   ```python
   DATABASES = {
       "default": {
           ...
           "ENGINE": "django.contrib.gis.db.backends.postgis",
       },
   }
   ```

3. Add `django.contrib.gis` to `INSTALLED_APPS`.

4. Install system libraries (already in the project Dockerfile if using the
   `postgis` image tag):

   ```bash
   # Debian/Ubuntu
   sudo apt-get install gdal-bin libgdal-dev
   ```

### Model fields

Replace `DecimalField` lat/lng pairs with a single `PointField`:

```python
from django.contrib.gis.db import models


class Venue(models.Model):
    ...
    location = models.PointField(null=True, blank=True, geography=True)
```

`geography=True` stores coordinates as WGS 84 (SRID 4326) and makes distance
calculations use great-circle math (metres on a sphere) rather than Cartesian.

### Creating points

```python
from django.contrib.gis.geos import Point

venue.location = Point(longitude, latitude, srid=4326)  # note: x=lng, y=lat
venue.save()
```

### Spatial queries

```python
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D


user_location = Point(-6.2603, 53.3498, srid=4326)  # Dublin

# Venues within 10 km
nearby = Venue.objects.filter(
    location__distance_lte=(user_location, D(km=10)),
)

# Order by distance, annotate with distance value
nearby_sorted = (
    Venue.objects.filter(location__isnull=False)
    .annotate(distance=Distance("location", user_location))
    .order_by("distance")
)
```

### Geocoding with GeoDjango

The geocoding task from above works unchanged — just store the result as a
`Point` instead of separate decimal fields:

```python
from django.contrib.gis.geos import Point


Venue.objects.filter(pk=venue_pk).update(
    location=Point(location.longitude, location.latitude, srid=4326),
)
```

### Admin integration

Use `GISModelAdmin` (or `GeoModelAdmin` on older Django) for an interactive
map widget in the admin:

```python
from django.contrib.gis import admin

@admin.register(Venue)
class VenueAdmin(admin.GISModelAdmin):
    ...
```

### References

- [GeoDjango documentation](https://docs.djangoproject.com/en/stable/ref/contrib/gis/)
- [PostGIS documentation](https://postgis.net/documentation/)
- [Spatial lookups reference](https://docs.djangoproject.com/en/stable/ref/contrib/gis/geoquerysets/)
