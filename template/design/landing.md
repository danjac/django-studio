# Landing Page

A public-facing marketing page with a hero, feature highlights, and call-to-action.
Build inline — no shipped template.

## Base template

Landing pages typically do not share the authenticated app shell. Use a
dedicated base or extend `base.html` with an empty `{% block sidebar %}`:

```html
{% extends "base.html" %}

{% block content %}
  ...
{% endblock content %}
```

If the landing page should have no sidebar at all, override or omit the sidebar
block (see `design/layout.md`).

## Hero section

```html
<section class="py-20 sm:py-32">
  <div class="mx-auto max-w-3xl px-4 text-center sm:px-6">
    <h1 class="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50 sm:text-6xl">
      {% translate "Headline goes here" %}
    </h1>
    <p class="mt-6 text-lg leading-8 text-zinc-600 dark:text-zinc-400">
      {% translate "A concise sub-headline describing the value proposition." %}
    </p>
    <div class="mt-10 flex items-center justify-center gap-4">
      <a href="{% url 'account_signup' %}" class="btn btn-primary">
        {% translate "Get started" %}
      </a>
      <a href="#features" class="btn btn-secondary">
        {% translate "Learn more" %}
      </a>
    </div>
  </div>
</section>
```

## Feature grid

```html
<section id="features" class="py-16 sm:py-24">
  <div class="mx-auto max-w-5xl px-4 sm:px-6">
    <h2 class="text-center text-2xl font-bold text-zinc-900 dark:text-zinc-50 sm:text-3xl">
      {% translate "Why choose us" %}
    </h2>
    <div class="mt-12 grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
      {# Repeat for each feature #}
      <div class="rounded-xl border border-(--color-border) bg-(--color-surface) p-6">
        {% heroicon_outline "bolt" class="size-8 text-primary-600 dark:text-primary-400" aria_hidden="true" %}
        <h3 class="mt-4 font-semibold text-zinc-900 dark:text-zinc-50">
          {% translate "Feature name" %}
        </h3>
        <p class="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
          {% translate "Short description of what this feature does." %}
        </p>
      </div>
    </div>
  </div>
</section>
```

## CTA section

```html
<section class="py-16 sm:py-24">
  <div class="mx-auto max-w-2xl px-4 text-center sm:px-6">
    <h2 class="text-2xl font-bold text-zinc-900 dark:text-zinc-50 sm:text-3xl">
      {% translate "Ready to get started?" %}
    </h2>
    <p class="mt-4 text-zinc-600 dark:text-zinc-400">
      {% translate "Join today and start doing the thing." %}
    </p>
    <a href="{% url 'account_signup' %}" class="btn btn-primary mt-8">
      {% translate "Create your account" %}
    </a>
  </div>
</section>
```

## View

Landing pages are typically public (`@require_safe` only, no `@login_required`):

```python
from django.template.response import TemplateResponse
from django.views.decorators.http import require_safe

from myapp.http.request import HttpRequest


@require_safe
def landing(request: HttpRequest) -> TemplateResponse:
    return TemplateResponse(request, "landing.html", {})
```

Wire it in `config/urls.py`:

```python
path("", views.landing, name="landing"),
```

## HTMX / Alpine integration

If sections load lazily or contain interactive elements, add HTMX or Alpine
attributes as needed. Keep the landing page lightweight — defer heavy dynamic
content to authenticated views.

## Design tokens

Use `--color-surface` / `--color-border` for cards. Use the primary colour for
CTAs (`btn-primary`). Hero text uses the standard Tailwind zinc scale for
light/dark compatibility.
