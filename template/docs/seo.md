# SEO

Search engine optimisation for this stack: what crawlers can reach, what they read
from each page, and how HTMX affects both. Run `/djs-seo` to audit a project
against this page.

## Contents

- [Key references](#key-references)
- [Does this project need SEO?](#does-this-project-need-seo)
- [robots.txt](#robotstxt)
- [Keeping pages out of search results](#keeping-pages-out-of-search-results)
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
in search results if other sites link to it. To keep a page out of results, see the
next section.

---

## Keeping pages out of search results

Robots directives tell search engines what to do with a page they have fetched:

| Directive | Effect |
|---|---|
| `noindex` | Leave the page out of search results |
| `nofollow` | Do not follow the links on the page |
| `noarchive` | Do not show a cached copy (Google no longer shows cached pages; other engines such as Bing still honour it) |

Combine them with commas: `noindex, nofollow`.

Send them in a meta tag for HTML pages, in `{% block meta %}`:

```html
{% block meta %}
  <meta name="robots" content="noindex">
{% endblock meta %}
```

The tag can depend on the object, for a public profile whose owner opted out of
search:

```html
{% block meta %}
  {% if not profile.searchable %}
    <meta name="robots" content="noindex">
  {% endif %}
{% endblock meta %}
```

Send the `X-Robots-Tag` header from the view when the response is not HTML (PDFs,
CSV exports, images) or the view already decides per request:

```python
@require_safe
def invoice_pdf(request: HttpRequest, pk: int) -> FileResponse:
    """Download an invoice as PDF."""
    ...
    response = FileResponse(pdf, filename=f"invoice-{pk}.pdf")
    response["X-Robots-Tag"] = "noindex, noarchive"
    return response
```

When several views set the same header, add a decorator to `<package_name>/seo.py`:

```python
import functools
from collections.abc import Callable

from django.http import HttpResponseBase

from my_package.http.request import HttpRequest

type View = Callable[..., HttpResponseBase]


def robots_tag(*directives: str) -> Callable[[View], View]:
    """Sets X-Robots-Tag on the view's response.

    Example:
        @robots_tag("noindex", "nofollow")
    """

    def decorator(view: View) -> View:
        @functools.wraps(view)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponseBase:
            response = view(request, *args, **kwargs)
            response["X-Robots-Tag"] = ", ".join(directives)
            return response

        return wrapper

    return decorator
```

A crawler sees a directive only on a page it is allowed to fetch, so keep the URL
allowed in `robots.txt`. To remove a page that is already indexed:

1. Leave it allowed in `robots.txt` and send `noindex`.
2. Wait for it to drop out; Search Console's URL Inspection shows when it has. Its
   Removals tool hides a URL for about six months when it cannot wait.
3. Keep `noindex` in place and the URL allowed. Disallowing it later hides the
   directive again, and the bare URL can return to results if other sites link to
   it.

`nofollow` on the page applies to every link on it. To mark a single link, use
`rel` on the `<a>`: `rel="ugc nofollow"` on links users submit (comments, profile
websites), `rel="sponsored"` on paid links.

---

## Titles and descriptions

Each page sets its own `<title>` with `{% title_tag %}` (see
`docs/django-templates.md`):

```html
{% block title %}{% title_tag post.title %}{% endblock %}
```

`{% meta_tags %}` renders the site-wide tags in `settings.META_TAGS`, including the
`META_DESCRIPTION` description. Add page-specific tags in `{% block meta %}`, which
`base.html` renders after them:

```html
{% block meta %}
  <meta name="description" content="{{ post.summary }}">
{% endblock meta %}
```

Before giving pages their own description, remove `"description"` from
`META_TAGS` in `config/settings.py`, so no page renders two, and the
`app.metaDescription` Helm value that sets it. Then set one in the `meta` block of
each public page, `home.html` included; pages behind a login need none.

Keep descriptions to one or two sentences (under about 160 characters) that
summarise the page, and translate them like any other user-facing string.

---

## Canonical URLs and social previews

A canonical link tells search engines which URL to index when the same page is
reachable under several, for example with `?page=2`, sort or filter parameters.
Open Graph tags control the preview shown when a page is shared.

Add both in the page's `meta` block:

```html
{% block meta %}
  <link rel="canonical" href="{{ request.scheme }}://{{ request.get_host }}{{ request.path }}">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{{ post.title }}">
  <meta property="og:description" content="{{ post.summary }}">
  <meta property="og:url" content="{{ request.scheme }}://{{ request.get_host }}{{ request.path }}">
  {% if post.cover %}
    <meta property="og:image" content="{{ post.cover.url }}">
  {% endif %}
{% endblock meta %}
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

Build the dict in the view and render it in the `meta` block:

```html
{% block meta %}{% json_ld article_schema %}{% endblock %}
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
