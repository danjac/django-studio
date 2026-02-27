# Cards

Template: `templates/card.html`

## Overview

`card.html` is a horizontal link card with an optional thumbnail image, a bold title, and an optional subtitle. All text truncates gracefully and highlights on hover.

## Context Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `url` | yes | Destination URL |
| `title` | yes | Primary heading (bold, 2-line clamp) |
| `subtitle` | no | Secondary line below title (1-line clamp) |
| `image_url` | no | Thumbnail src — 64×64px, rounded |
| `target_blank` | no | If truthy, opens in a new tab |

## Usage

### In a List View

```html
{% for item in object_list %}
  <article>
    {% include "card.html" with url=item.get_absolute_url title=item.name subtitle=item.author image_url=item.cover_url %}
  </article>
{% empty %}
  <p class="text-zinc-500">No items yet.</p>
{% endfor %}
```

### Standalone

```python
# views.py
context = {
    "url": podcast.get_absolute_url(),
    "title": podcast.title,
    "subtitle": podcast.owner,
    "image_url": podcast.cover_url,
}
```

```html
{% include "card.html" with url=url title=title subtitle=subtitle image_url=image_url %}
```

## Styling

The card applies hover color via the `group` / `group-hover:` pattern — no JavaScript needed. Both title and subtitle shift to `indigo-600` (`indigo-400` in dark mode) on hover.

## Custom Card Layouts

For different card shapes (vertical, featured, etc.), build a custom include rather than extending this template. Keep cards simple: one layout per template file.

### Vertical Card Example

```html
{# templates/card_vertical.html #}
<a href="{{ url }}" title="{{ title }}" class="group flex flex-col gap-3">
  {% if image_url %}
    <img src="{{ image_url }}" alt="" class="aspect-square w-full rounded-xl object-cover" loading="lazy">
  {% endif %}
  <div>
    <h2 class="font-bold group-hover:text-indigo-600 dark:group-hover:text-indigo-400">{{ title }}</h2>
    {% if subtitle %}<p class="text-sm text-zinc-500">{{ subtitle }}</p>{% endif %}
  </div>
</a>
```

## HTMX Infinite Scroll / Load More

Wrap the card list in a container and append new results with HTMX:

```html
<ul id="results" class="space-y-4">
  {% for item in page.object_list %}
    <li>{% include "card.html" with url=item.get_absolute_url title=item.name %}</li>
  {% endfor %}
  {% if page.has_next %}
    <li
      hx-get="{{ request.path }}?page={{ page.next_page_number }}"
      hx-trigger="intersect once"
      hx-target="#results"
      hx-swap="beforeend"
    ></li>
  {% endif %}
</ul>
```
