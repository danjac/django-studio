# SEO

Search engine optimisation for this stack: what crawlers can reach, what they read
from each page, and how HTMX affects both. Run `/djs-seo` to audit a project
against this page.

## Contents

- [Key references](#key-references)
- [Does this project need SEO?](#does-this-project-need-seo)
- [robots.txt](#robotstxt)
- [Titles and descriptions](#titles-and-descriptions)
- [Canonical URLs and social previews](#canonical-urls-and-social-previews)
- [Sitemaps](#sitemaps)
- [HTMX](#htmx)
- [Status codes](#status-codes)
- [Structured data](#structured-data)
- [Localisation](#localisation)
- [Testing](#testing)

## Key references

- [Google Search Central: SEO starter guide](https://developers.google.com/search/docs/fundamentals/seo-starter-guide)
- [robots.txt specification (RFC 9309)](https://www.rfc-editor.org/rfc/rfc9309)
- [Django sitemap framework](https://docs.djangoproject.com/en/stable/ref/contrib/sitemaps/)
- [Open Graph protocol](https://ogp.me/)
- [schema.org](https://schema.org/) and Google's
  [Rich Results Test](https://search.google.com/test/rich-results)

---

## Does this project need SEO?

SEO applies only to pages an anonymous visitor can reach and that you want found
through search. List them first: usually the landing page, about page and any public
content generated from models (articles, listings, profiles).

If almost everything sits behind a login, the shipped setup is enough: `robots.txt`
allows the landing and about pages and disallows the rest. Skip sitemaps and
structured data until the project has public content to index.

---

## robots.txt

`views.robots` in `<package_name>/views.py` serves an allow-list: each named URL gets
an `Allow:` line, and `Disallow: /` blocks everything else. A new public page stays
hidden from crawlers until you add its URL name:

```python
*[f"Allow: {reverse(name)}$" for name in ["index", "about", "pricing"]],
```

The `$` anchors the rule to that exact path. For a section of public pages generated
from models, allow the prefix without `$`, so `/posts/` covers `/posts/<slug>/`:

```python
"Allow: /posts/",
```

`robots.txt` controls crawling, not indexing: a disallowed URL can still be listed
in search results if other sites link to it. Add
`<meta name="robots" content="noindex">` to a public page that must stay out of
results, and leave it crawlable so the crawler can read the tag.

---

## Titles and descriptions

Each page sets its own `<title>` with `{% title_tag %}` (see
`docs/django-templates.md`):

```html
{% block title %}{% title_tag post.title %}{% endblock %}
```

`{% meta_tags %}` renders `settings.META_TAGS`, so every page shares the
`META_DESCRIPTION` description by default. When public pages need their own
description, let the tag take overrides and give `base.html` a block around it.

In `<package_name>/templatetags.py`, replace `meta_tags` (drop `@functools.cache`,
since the output now varies per page):

```python
@register.simple_tag
def meta_tags(**overrides: str) -> str:
    """Renders META tags from settings including HTMX config.

    Keyword arguments override entries in settings.META_TAGS, e.g.
    {% meta_tags description=post.summary %}
    """
    tags = [
        *[
            {"name": key, "content": value}
            for key, value in (settings.META_TAGS | overrides).items()
        ],
        {
            "name": "htmx-config",
            "content": json.dumps(settings.HTMX_CONFIG),
        },
    ]
    ...
```

In `templates/base.html`:

```html
{% block meta_tags %}{% meta_tags %}{% endblock meta_tags %}
```

In a public page:

```html
{% block meta_tags %}{% meta_tags description=post.summary %}{% endblock meta_tags %}
```

Keep descriptions to one or two sentences (under about 160 characters) that
summarise the page, and translate them like any other user-facing string.

---

## Canonical URLs and social previews

A canonical link tells search engines which URL to index when the same page is
reachable under several, for example with `?page=2`, sort or filter parameters.
Open Graph tags control the preview shown when a page is shared.

Add a `head` block to `templates/base.html`, after `{% meta_tags %}`:

```html
{% block head %}{% endblock head %}
```

Then fill it in each public page:

```html
{% block head %}
  <link rel="canonical" href="{{ request.scheme }}://{{ request.get_host }}{{ request.path }}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{{ post.title }}">
  <meta property="og:description" content="{{ post.summary }}">
  <meta property="og:url" content="{{ request.scheme }}://{{ request.get_host }}{{ request.path }}">
  {% if post.cover %}
    <meta property="og:image" content="{{ post.cover.url }}">
  {% endif %}
{% endblock head %}
```

`og:image` must be an absolute URL. Media served from object storage already is;
see `docs/file-storage.md`.

---

## Sitemaps

Add a sitemap when the project has public pages generated from models. Crawlers
find a landing page and an about page without one, and each sitemap is a set of
querysets you have to keep in step with what is public.

`django.contrib.sitemaps` is already in `INSTALLED_APPS`. Add a `sitemaps.py` to the
app that owns the content:

```python
import datetime

from django.contrib.sitemaps import Sitemap
from django.db.models import QuerySet

from my_package.posts.models import Post


class PostSitemap(Sitemap):
    """Published posts."""

    def items(self) -> QuerySet[Post]:
        """Return the posts to list."""
        return Post.objects.published()

    def lastmod(self, obj: Post) -> datetime.datetime:
        """Return when the post last changed."""
        return obj.updated
```

The model needs `get_absolute_url()`. Wire the sitemap in `config/urls.py`:

```python
from django.contrib.sitemaps.views import sitemap

from my_package.posts.sitemaps import PostSitemap

path(
    "sitemap.xml",
    sitemap,
    {"sitemaps": {"posts": PostSitemap}},
    name="sitemap",
),
```

Then point to it from `robots.txt`, and allow it, in `views.robots`:

```python
def robots(request: HttpRequest) -> TextResponse:
    """Serve robots.txt."""
    return TextResponse(
        "\n".join(
            [
                "User-Agent: *",
                *[f"Allow: {reverse(name)}$" for name in ["index", "about", "sitemap"]],
                "Allow: /posts/",
                "Disallow: /",
                f"Sitemap: {request.build_absolute_uri(reverse('sitemap'))}",
            ]
        ),
    )
```

The `Sitemap:` URL must be absolute. The sitemap framework takes the domain from
`django.contrib.sites`, so set the `Site` record's domain on each deployment.

---

## HTMX

Crawlers read the HTML of a plain `GET`. Content that HTMX loads after the page
arrives may not be indexed.

- Render a public page's main content in the first response. Do not load it with
  `hx-trigger="load"` or `revealed`; keep those for secondary content such as
  comments or related items.
- Every URL in an `hx-push-url` or boosted link must return the full page on a
  direct `GET`. The `request.htmx|yesno:"hx_base.html,base.html"` pattern and
  `render_partial_response` both do this (see `docs/htmx.md`).
- `HtmxCacheMiddleware` sets `Vary: HX-Request`, so a cache never serves a partial
  to a crawler. Keep it in `MIDDLEWARE`.
- Paginate public lists with real `?page=N` links in `href`, not only
  `hx-get`, so crawlers can follow them (see `docs/pagination.md`).

---

## Status codes

Search engines index pages that return `200`, so error pages must not.

- Look up public objects with `get_object_or_404`, so a missing object returns
  `404`, not an empty `200` page.
- When a public URL changes, redirect the old one with a permanent redirect
  (`redirect(..., permanent=True)`, `301`).
- Pages behind `@login_required` redirect anonymous visitors to the login page, and
  crawlers follow that redirect: keep them disallowed in `robots.txt`.

---

## Structured data

JSON-LD describes a page's content to search engines (an article, product, event or
organisation) and can earn rich results. Add it only where a model maps clearly to a
[schema.org](https://schema.org/) type.

Add a tag to the owning app's template tags (see
`docs/django-templates.md#custom-template-tags-and-filters`):

```python
@register.simple_tag
def json_ld(data: dict) -> str:
    """Renders a JSON-LD script block."""
    content = (
        json.dumps(data, cls=DjangoJSONEncoder)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )
    # JSON escaped above, so it cannot close the script element.
    return format_html(
        '<script type="application/ld+json">{}</script>',
        mark_safe(content),  # noqa: S308
    )
```

Build the dict in the view and render it in the `head` block:

```html
{% block head %}{% json_ld article_schema %}{% endblock head %}
```

A `type="application/ld+json"` block is data, not script, so it needs no CSP nonce.
Check the output with the Rich Results Test.

---

## Localisation

The project picks the language from the language cookie or the `Accept-Language`
header, so each page has one URL and crawlers index it in `LANGUAGE_CODE`. That is
enough unless you need translated pages to rank in other languages' search results.
In that case, move public URLs into `i18n_patterns` so each language has its own URL,
and add `<link rel="alternate" hreflang="...">` links between them. See
`docs/localization.md`.

---

## Testing

Test what crawlers depend on, alongside the view tests:

```python
@pytest.mark.django_db
class TestRobots:
    def test_allows_public_pages(self, client):
        response = client.get(reverse("robots"))
        assert f"Allow: {reverse('pricing')}$" in response.content.decode()


@pytest.mark.django_db
class TestPostDetail:
    def test_meta_description(self, client):
        post = PostFactory(summary="A short summary")
        response = client.get(post.get_absolute_url())
        assertContains(response, '<meta name="description" content="A short summary">')
```

For the rendered site, run Lighthouse's SEO category against a deployed page, and
use Google Search Console to see what is crawled and indexed.
