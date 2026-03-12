# Cards

Cards are a **pattern**, not a shipped template. Build them inline for your specific
data shape — image dimensions, aspect ratios, and thumbnail handling vary too much per
project to abstract usefully.

## Structure

A card is a linked tile inside `grid.html`. At minimum:

```html
{% fragment "grid.html#item" %}
  <a
    href="{{ item.get_absolute_url }}"
    class="group flex flex-col overflow-hidden rounded-xl border border-(--color-border) bg-(--color-surface) transition-shadow hover:shadow-md"
  >
    <div class="flex flex-col gap-1 p-4">
      <h2 class="line-clamp-2 font-bold leading-tight group-hover:text-primary-600 dark:group-hover:text-primary-400">
        {{ item.title }}
      </h2>
    </div>
  </a>
{% endfragment %}
```

## With sorl-thumbnail

Install `sorl-thumbnail` first (`uv add sorl-thumbnail`), then add `"sorl.thumbnail"` to
`INSTALLED_APPS`.

```html
{% load thumbnail %}

{% fragment "grid.html#item" %}
  <a
    href="{{ photo.get_absolute_url }}"
    class="group flex flex-col overflow-hidden rounded-xl border border-(--color-border) bg-(--color-surface) transition-shadow hover:shadow-md"
  >
    {% thumbnail photo.image "640x360" crop="center" as thumb %}
      <img
        src="{{ thumb.url }}"
        alt=""
        width="{{ thumb.width }}"
        height="{{ thumb.height }}"
        class="w-full object-cover"
        loading="lazy"
      >
    {% empty %}
      <div class="aspect-video w-full bg-(--color-border)"></div>
    {% endthumbnail %}
    <div class="flex flex-col gap-1 p-4">
      <h2 class="line-clamp-2 font-bold leading-tight group-hover:text-primary-600 dark:group-hover:text-primary-400">
        {{ photo.title }}
      </h2>
    </div>
  </a>
{% endfragment %}
```

Using `sorl-thumbnail`:
- Always provide explicit `width` and `height` attributes from the thumbnail object (satisfies accessibility linting).
- Use `{% empty %}` to render a placeholder when no image is set.
- Choose a fixed geometry string (`"640x360"`) matching your grid column width at ~2x for HiDPI.

## Paginated grid example

```python
# views.py
def photo_list(request):
    return render_paginated_response(request, "photos/list.html", Photo.objects.all())
```

```html
{# photos/list.html #}
{% load thumbnail %}

{% partialdef pagination inline %}
  {% fragment "paginate.html" %}
    {% fragment "grid.html" %}
      {% for photo in page %}
        {% fragment "grid.html#item" %}
          <a href="{{ photo.get_absolute_url }}" class="group flex flex-col overflow-hidden rounded-xl border border-(--color-border) bg-(--color-surface) transition-shadow hover:shadow-md">
            {% thumbnail photo.image "640x360" crop="center" as thumb %}
              <img src="{{ thumb.url }}" alt="" width="{{ thumb.width }}" height="{{ thumb.height }}" class="w-full object-cover" loading="lazy">
            {% empty %}
              <div class="aspect-video w-full bg-(--color-border)"></div>
            {% endthumbnail %}
            <div class="flex flex-col gap-1 p-4">
              <h2 class="line-clamp-2 font-bold leading-tight group-hover:text-primary-600 dark:group-hover:text-primary-400">{{ photo.title }}</h2>
            </div>
          </a>
        {% endfragment %}
      {% empty %}
        {% fragment "grid.html#empty" %}{% translate "No photos yet." %}{% endfragment %}
      {% endfor %}
    {% endfragment %}
  {% endfragment %}
{% endpartialdef pagination %}
```

## Design tokens

Cards use `--color-surface` for the background and `--color-border` for the outline.
Hover adds a drop shadow and shifts title text to the primary brand color.
