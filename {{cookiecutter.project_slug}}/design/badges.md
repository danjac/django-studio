# Badges

There is no dedicated `badge.html` template - badges are small enough to inline. This doc defines the standard patterns to use consistently.

## Colour Variants

```html
{# Status: neutral #}
<span class="inline-flex items-center rounded-full bg-zinc-100 px-2.5 py-0.5 text-xs font-semibold text-zinc-700 dark:bg-zinc-800 dark:text-zinc-300">
  Draft
</span>

{# Status: info (blue) #}
<span class="inline-flex items-center rounded-full bg-sky-100 px-2.5 py-0.5 text-xs font-semibold text-sky-700 dark:bg-sky-950 dark:text-sky-300">
  In progress
</span>

{# Status: success (green) #}
<span class="inline-flex items-center rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
  Published
</span>

{# Status: warning (amber) #}
<span class="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-700 dark:bg-amber-950 dark:text-amber-300">
  Pending review
</span>

{# Status: danger (rose) #}
<span class="inline-flex items-center rounded-full bg-rose-100 px-2.5 py-0.5 text-xs font-semibold text-rose-700 dark:bg-rose-950 dark:text-rose-300">
  Rejected
</span>
```

## With Icon

```html
{% load heroicons %}
<span class="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">
  {% heroicon_micro "check" aria-hidden="true" %}
  Verified
</span>
```

Use `heroicon_micro` (16px) for icons inside badges.

## Count / Notification Dot

```html
{# Numeric count - e.g. unread items #}
<span class="inline-flex size-5 items-center justify-center rounded-full bg-indigo-600 text-xs font-bold text-white">
  {{ count }}
</span>

{# Dot - presence indicator, no number #}
<span class="size-2 rounded-full bg-emerald-500" aria-label="Online"></span>
```

## Tag / Category Chip

Tags are interactive (filterable) or static:

```html
{# Static tag #}
<span class="inline-flex items-center rounded-md bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
  Python
</span>

{# Interactive tag - links to filtered list #}
<a
  href="{% url 'posts:list' %}?tag={{ tag.slug }}"
  class="inline-flex items-center rounded-md bg-zinc-100 px-2 py-1 text-xs font-medium text-zinc-600 transition-colors hover:bg-indigo-100 hover:text-indigo-700 dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-indigo-950 dark:hover:text-indigo-300"
>
  {{ tag.name }}
</a>
```

## In a List

Badges commonly appear alongside card titles or table rows:

```html
<div class="flex items-center gap-2">
  <h2 class="font-bold">{{ post.title }}</h2>
  {% if not post.published %}
    <span class="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-semibold text-amber-700 dark:bg-amber-950 dark:text-amber-300">
      Draft
    </span>
  {% endif %}
</div>
```

## Accessibility

- Badges are purely visual - the surrounding context should convey the meaning in text.
- For colour-only status indicators (dot), add `aria-label` to provide a text alternative.
- Never use badge colour alone as the only signal - pair it with a text label.
