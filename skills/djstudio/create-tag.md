Add a template tag to an existing app or the root `templatetags.py` module.
See `docs/Django-Templates.md` for the tag type reference and testing conventions.

**Parsing arguments:**

- Two words (e.g. `create-tag blog my_tag`): first is `<app_name>`, second is `<tag_name>`.
- One word (e.g. `create-tag my_tag`): no app — add to the root `<package_name>/templatetags.py`.

**Before writing any code, ask the user: *What should this tag do?*** If the description is
ambiguous, determine the tag type first:

Pick the simplest type that fits — in this order of preference:

| Priority | Type | Use when |
|----------|------|----------|
| 1 | `@register.simple_tag` | Returns a value; no template rendering required |
| 2 | `@register.simple_tag(takes_context=True)` | Returns a value but needs `request` or context variables |
| 3 | `@register.simple_block_tag` | Wraps or transforms a block of template content (Django 5.2+) |
| 4 | `@register.inclusion_tag("template.html")` | Renders a sub-template and returns its output |
| 5 | Custom `template.Node` subclass | Requires compile-time logic that none of the above can handle |

**`simple_block_tag` first, custom `Node` last.**
If the tag needs to wrap or inject content, reach for `simple_block_tag` before considering
a custom `Node`. The built-in `fragment` tag in `<package_name>/templatetags.py` is a
working example: it wraps a block of content and renders it inside an include template.
Only escalate to a custom `Node` if `simple_block_tag` genuinely cannot express the logic.

If the description suggests a custom `Node` subclass is needed, **stop and discuss** the
approach with the user before writing any code.

---

**Steps:**

1. **Resolve the target file:**

   | Scenario | File |
   |----------|------|
   | App-level | `<package_name>/<app_name>/templatetags/<app_name>.py` |
   | Root (no app) | `<package_name>/templatetags.py` |

   Check whether the file exists before writing:
   - If it exists, append the new tag to it.
   - If the app-level file does not exist, create it with:
     ```python
     from django import template

     register = template.Library()
     ```
     Also create `<package_name>/<app_name>/templatetags/__init__.py` (empty) if missing.

   The root `<package_name>/templatetags.py` ships with every project — always append,
   never recreate.

2. **Write the tag function** and register it using the chosen type.

   `simple_tag`:
   ```python
   @register.simple_tag
   def <tag_name>(<args>) -> <ReturnType>:
       """One-line summary.

       Example:
           {% <tag_name> arg %}
       """
       ...
   ```

   `simple_tag(takes_context=True)`:
   ```python
   @register.simple_tag(takes_context=True)
   def <tag_name>(context: "RequestContext", <args>) -> <ReturnType>:
       """One-line summary."""
       ...
   ```

   `simple_block_tag` (Django 6):
   ```python
   @register.simple_block_tag
   def <tag_name>(content: str, <args>) -> "SafeString":
       """One-line summary."""
       ...
   ```

   `inclusion_tag`:
   ```python
   @register.inclusion_tag("<template_path>.html", takes_context=True)
   def <tag_name>(context: "RequestContext", <args>) -> dict:
       """One-line summary."""
       return {...}
   ```
   Create the companion template at `templates/<template_path>.html`.

   Use `TYPE_CHECKING` guards for type-only imports (`RequestContext`, `SafeString`, etc.).
   Tags that produce HTML must use `format_html` or `mark_safe` — never return raw
   f-strings or string concatenations containing user-supplied data.

3. **Write tests** in:
   - App-level: `<package_name>/<app_name>/tests/test_template_tags.py`
   - Root: `<package_name>/tests/test_template_tags.py`

   Test the tag function directly — do not instantiate `Template`/`Context` unless the test
   genuinely requires full template rendering:
   ```python
   from <package_name>.<app_name>.templatetags.<app_name> import <tag_name>

   def test_<tag_name>():
       assert <tag_name>(...) == expected
   ```

   For `inclusion_tag`, assert the returned context dict, not the rendered HTML.

4. Verify: `just check-all`

---

## Help

**djstudio create-tag [<app_name>] <tag_name>**

Adds a template tag to an app's templatetags module or to the root `templatetags.py`.

With `<app_name>`: adds to `<app_name>/templatetags/<app_name>.py` (created if missing).
Without `<app_name>`: adds to the root `<package_name>/templatetags.py`.

Prompts for a description before writing, then picks the simplest fitting type:
`simple_tag`, `simple_block_tag`, `inclusion_tag`, or custom `Node` (discussed
with the user before implementing).

Writes the tag function, any required companion template, and tests.

Examples:
  /djstudio create-tag blog my_tag    # blog/templatetags/blog.py
  /djstudio create-tag my_tag         # <package_name>/templatetags.py (root)
