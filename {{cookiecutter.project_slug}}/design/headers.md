# Page Header

`templates/header.html` — reusable page-level heading with optional subtitle.

## Usage

```django
{% include "header.html" with title="Privacy Policy" %}
{% include "header.html" with title="About" subtitle="Learn more about this project" %}
{% fragment "header.html" %}
  content goes here
{% endfragment %}
```

## Variables

| Variable   | Required | Description                      |
| ---------- | -------- | -------------------------------- |
| `title`    | yes      | Main page heading                |
| `subtitle` | no       | Secondary descriptive text below |

## Notes

- Use at the top of page `{% block content %}` for consistent page layout.
- Wrap translated strings with `_()` when including from a template that loads `i18n`.
