**/dj-create-tag [<app_name>] <tag_name>**

Adds a template tag to an app's templatetags module or to the root `templatetags.py`.

With `<app_name>`: adds to `<app_name>/templatetags/<app_name>.py` (created if missing).
Without `<app_name>`: adds to the root `<package_name>/templatetags.py`.

Prompts for a description before writing, then picks the simplest fitting type:
`simple_tag`, `simple_block_tag`, `inclusion_tag`, or custom `Node` (discussed
with the user before implementing).

Writes the tag function, any required companion template, and tests.

Examples:
  /dj-create-tag blog my_tag    # blog/templatetags/blog.py
  /dj-create-tag my_tag         # <package_name>/templatetags.py (root)
