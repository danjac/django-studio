# SEO audit finds seeded gaps on a public page

Covers `/djs-seo`. The setup describes the project as a public product whose
pricing page must rank in search, then adds a public `pricing` page with three
seeded gaps: robots.txt does not allow it, it sets no title of its own, and its
main content loads with `hx-trigger="load"`. The audit must report all three as
VIOLATION and change no code.

## Setup

```sh
perl -0pi -e 's/_What problem does this project solve.*?sentences\._/My App is a hosted invoicing tool for freelancers. Anyone can read the landing, about and pricing pages, and the pricing page must rank in search results. Everything else is behind a login./s' \
  docs/this-project.md
cat >> my_app/views.py <<'EOF'


@require_safe
def pricing(request: HttpRequest) -> TemplateResponse:
    """Public pricing page."""
    return TemplateResponse(request, "pricing.html")


@require_safe
def pricing_plans(request: HttpRequest) -> TemplateResponse:
    """Pricing plans, loaded into the pricing page."""
    return TemplateResponse(request, "pricing_plans.html")
EOF
cat > templates/pricing.html <<'EOF'
{% extends "base.html" %}
{% load i18n %}

{% block content %}
  {% include "header.html" with title=_("Pricing") %}
  <div hx-get="{% url 'pricing_plans' %}" hx-trigger="load"></div>
{% endblock content %}
EOF
cat > templates/pricing_plans.html <<'EOF'
{% load i18n %}
<ul>
  <li>{% translate "Free: 3 invoices a month" %}</li>
  <li>{% translate "Pro: unlimited invoices" %}</li>
</ul>
EOF
sed -i 's|^    path("about/", views.about, name="about"),$|&\n    path("pricing/", views.pricing, name="pricing"),\n    path("pricing/plans/", views.pricing_plans, name="pricing_plans"),|' \
  config/urls.py
just dj check
```

## Prompt

```text
/djs-seo

Report only. Do not fix anything and do not edit any file, even for VIOLATION
findings: the report is the output of this run.
```

## Check

```sh
report="$EVAL_BUILD_OUTPUT"
violations=$(sed -n '/VIOLATION/,/WARNING/p' "$report")
echo "$violations"
echo "$violations" | grep -q "pricing"
echo "$violations" | grep -qi "robots"
echo "$violations" | grep -qi "title"
echo "$violations" | grep -q "hx-trigger"
git diff --quiet HEAD -- my_app config templates docs
```

## Review

```text
An SEO audit of this Django project (package `my_app`) produced the report below.
Check the report against the code.

Verify these facts:

1. The report lists `/pricing/` as a public page and does not list login-only
   views (account pages, `users` views) as public.
2. The report flags, as VIOLATION, that `views.robots` in `my_app/views.py` does
   not allow `/pricing/`, that `templates/pricing.html` sets no title of its own,
   and that its main content loads with `hx-trigger="load"`.
3. Every VIOLATION in the report points at code that exists and matches the
   description. Quote the code for each.
4. The report does not recommend a sitemap as anything above ADVISORY.

Report:

{build_output}
```
