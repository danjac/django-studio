# Page Header

`templates/header.html` - reusable page-level heading.

## Usage

```django
{# Simple title only #}
{% include "header.html" with title=_("Privacy Policy") %}

{# Title with action buttons on the right #}
{% fragment "header.html" title=_("Venues") %}
  <a href="{% url 'venues:create' %}" class="btn btn-primary">{% translate "Add Venue" %}</a>
{% endfragment %}
```

## Variables

| Variable | Required | Description       |
| -------- | -------- | ----------------- |
| `title`  | yes      | Main page heading |

## Notes

- Use at the top of page `{% block content %}` for consistent page layout.
- Wrap translated strings with `_()` when including from a template that loads `i18n`.
- For content below the header (forms, body text), wrap in `<div class="mt-6">` to maintain consistent spacing.
- Use `{% fragment %}` when you need action buttons on the right side of the header; use `{% include %}` for title-only pages.
