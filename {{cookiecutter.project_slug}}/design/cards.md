# Cards

Template: `templates/card.html`

## Overview

`card.html` is a vertical tile for **grid layouts** - image on top (16:9), title and optional subtitle below, with a hover shadow. Use it inside `grid.html#item`.

## Context Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `url` | yes | Card link href |
| `title` | yes | Primary heading (bold, 2-line clamp) |
| `subtitle` | no | Secondary line below title (1-line clamp) |
| `image_url` | no | Cover image URL, displayed at 16:9 aspect ratio |
| `target_blank` | no | If truthy, opens in a new tab |

## Usage

### Paginated grid

```python
# views.py
def photo_list(request):
    return render_paginated_response(request, "photos/list.html", Photo.objects.all())
```

```html
{# photos/list.html #}
{% partialdef pagination inline %}
  {% fragment "paginate.html" %}
    {% fragment "grid.html" %}
      {% for photo in page %}
        {% fragment "grid.html#item" %}
          {% include "card.html" with url=photo.get_absolute_url title=photo.title image_url=photo.image_url %}
        {% endfragment %}
      {% empty %}
        {% fragment "grid.html#empty" %}No photos yet.{% endfragment %}
      {% endfor %}
    {% endfragment %}
  {% endfragment %}
{% endpartialdef pagination %}
```

### Unpaginated grid

```html
{% fragment "grid.html" %}
  {% for item in object_list %}
    {% fragment "grid.html#item" %}
      {% include "card.html" with url=item.get_absolute_url title=item.name image_url=item.cover_url %}
    {% endfragment %}
  {% empty %}
    {% fragment "grid.html#empty" %}Nothing here yet.{% endfragment %}
  {% endfor %}
{% endfragment %}
```

## Styling

Cards use design tokens: `--color-surface` for the background, `--color-border` for the border outline. Hover adds a drop shadow and shifts title text to indigo.

For different card shapes (square crop, no image, extra metadata lines), build a custom include rather than modifying this template. Keep one layout per template file.
