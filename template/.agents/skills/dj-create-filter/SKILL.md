---
description: Add a template filter with correct escaping flags
---

Add a template filter to an existing app or the root `templatetags.py` module.
See `docs/django-templates.md` for filter conventions and testing patterns.

**Parsing arguments:**

- Two words (e.g. `blog my_filter`): first is `<app_name>`, second is `<filter_name>`.
- One word (e.g. `my_filter`): no app — add to the root `<package_name>/templatetags.py`.

**Before writing any code, ask the user: *What should this filter do?*** If the description
is ambiguous, clarify:

- Does the filter return HTML that should be marked safe? → use `is_safe=True`
- Does it need to know whether autoescaping is active? → use `needs_autoescape=True`
- Does it only transform a plain value (string, number, date)? → plain filter, no flags

---

**Steps:**

1. **Resolve the target file:**

   | Scenario | File |
   |----------|------|
   | App-level | `<package_name>/<app_name>/templatetags/<app_name>.py` |
   | Root (no app) | `<package_name>/templatetags.py` |

   Check whether the file exists before writing:
   - If it exists, append the new filter to it.
   - If the app-level file does not exist, create it with:
     ```python
     from django import template

     register = template.Library()
     ```
     Also create `<package_name>/<app_name>/templatetags/__init__.py` (empty) if missing.

   The root `<package_name>/templatetags.py` ships with every project — always append,
   never recreate.

2. **Write the filter function** and register it using the appropriate decorator.

   Plain filter:
   ```python
   @register.filter
   def <filter_name>(value: <InputType>) -> <ReturnType>:
       """One-line summary.

       Example:
           {{ value|<filter_name> }}
       """
       ...
   ```

   Filter that returns trusted HTML (`is_safe=True`):
   ```python
   @register.filter(is_safe=True)
   def <filter_name>(value: str) -> str:
       """One-line summary."""
       ...
   ```

   Filter that is aware of autoescaping (`needs_autoescape=True`):
   ```python
   from django.utils.html import conditional_escape, mark_safe

   @register.filter(needs_autoescape=True)
   def <filter_name>(value: str, autoescape: bool = True) -> str:
       """One-line summary."""
       esc = conditional_escape if autoescape else str
       result = esc(value)
       return mark_safe(result)
   ```

   Filters that produce HTML must use `format_html` (single fragment) or
   `format_html_join` (list of fragments) — both escape every interpolated value and
   return a `SafeString`. Never return raw f-strings or string concatenations containing
   user-supplied data. `format_html` already calls `mark_safe` internally — never wrap
   its output in `mark_safe`. Only call `mark_safe` directly on strings you have
   pre-sanitized externally (e.g. with `nh3`) or via `conditional_escape` (as in the
   `needs_autoescape` pattern above). **IMPORTANT — XSS risk: never pass user-supplied
   data to `mark_safe` or the `|safe` template filter — they are equivalent and equally
   dangerous.**

3. **Write tests** in:
   - App-level: `<package_name>/<app_name>/tests/test_template_tags.py`
   - Root: `<package_name>/tests/test_template_tags.py`

   Import and call the filter function directly — do not instantiate `Template`/`Context`
   unless the test genuinely requires full template rendering:
   ```python
   from <package_name>.<app_name>.templatetags.<app_name> import <filter_name>

   def test_<filter_name>():
       assert <filter_name>(value) == expected
   ```

   For `needs_autoescape` filters, test with both `autoescape=True` and `autoescape=False`
   to confirm the escaping behaviour is correct in both modes.

4. Verify: `just check-all`
