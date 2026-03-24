**/dj-create-filter [<app_name>] <filter_name>**

Adds a template filter to an app's templatetags module or to the root `templatetags.py`.

With `<app_name>`: adds to `<app_name>/templatetags/<app_name>.py` (created if missing).
Without `<app_name>`: adds to the root `<package_name>/templatetags.py`.

Prompts for a description before writing, then picks the correct decorator flags:
plain `@register.filter`, `is_safe=True`, or `needs_autoescape=True`.

Writes the filter function and tests.

Examples:
  /dj-create-filter blog my_filter    # blog/templatetags/blog.py
  /dj-create-filter my_filter         # <package_name>/templatetags.py (root)
