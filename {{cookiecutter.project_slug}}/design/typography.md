# Typography

Template: `templates/markdown.html`

## Markdown / Prose

`markdown.html` renders pre-processed HTML (from a markdown library) using the Tailwind Typography plugin (`prose`).

### Context Variables

| Variable   | Required | Description                                    |
| ---------- | -------- | ---------------------------------------------- |
| `markdown` | yes      | Sanitized HTML string from a markdown renderer |

### Usage

Pre-render markdown to HTML in the view, then pass it to the template:

```python
# views.py — using python-markdown + bleach for sanitization
import markdown
import nh3
from markdown_it import MarkdownIt
from markdownify import markdownify

ALLOWED_TAGS = {"p", "h2", "h3", "h4", "pre", "code", "hr"}

_markdown = MarkdownIt("commonmark", {
  "linkify": True,
  "typographer": True,
}).enable(
        [
            "linkify",
            "replacements",
            "smartquotes",
        ]
    )


def my_view(request, pk):
    obj = get_object_or_404(MyModel, pk=pk)
    rendered = markdownify(content) if nh3.is_html(content) else content
    safe_html = nh3.clean(
        _markdown().render(content),
        tags=ALLOWED_TAGS,
    )
    return TemplateResponse(request, "my_detail.html", {"markdown": safe_html})
```

```html
{# my_detail.html #} {% include "markdown.html" with markdown=markdown %}
```

### Prose Classes

The `prose prose-zinc dark:prose-invert` classes from Tailwind Typography apply opinionated styles to all descendant HTML elements. Customise via Tailwind config:

```js
// tailwind.config.js
module.exports = {
  plugins: [require("@tailwindcss/typography")],
  theme: {
    extend: {
      typography: {
        DEFAULT: {
          css: {
            maxWidth: "none", // remove default max-width
          },
        },
      },
    },
  },
};
```

### HTMX Disable

The `hx-disable="true"` attribute on the prose wrapper prevents HTMX from intercepting links inside the markdown content. This is intentional — markdown often contains external links that should navigate normally.

---

## Heading Scale

| Element         | Classes                                                  | Use                |
| --------------- | -------------------------------------------------------- | ------------------ |
| Page title      | `text-2xl font-bold`                                     | One per page       |
| Section heading | `text-xl font-semibold`                                  | Subsections        |
| Card title      | `text-base font-bold leading-tight`                      | Card `.card.html`  |
| Muted label     | `text-sm font-semibold text-zinc-500 dark:text-zinc-400` | Metadata, captions |

## Text Colours

```html
<!-- Primary text (inherits from body) -->
<p class="text-zinc-900 dark:text-zinc-100">Main content</p>

<!-- Secondary / muted text -->
<p class="text-zinc-500 dark:text-zinc-400">Captions, timestamps, metadata</p>

<!-- Error text -->
<p class="text-rose-600 dark:text-rose-400">Validation error</p>

<!-- Success text -->
<p class="text-emerald-600 dark:text-emerald-400">Confirmation</p>
```

## Link Style

The `link` class (defined in `tailwind/links.css`) applies the standard indigo link style with hover and focus states:

```html
<a href="/about/" class="link">About</a>
```

Use `link` for inline text links. Use `btn` for call-to-action links that should look like buttons.
