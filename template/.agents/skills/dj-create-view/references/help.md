**/dj-create-view [<app_name>] <view_name>**

Adds a view function, template, and URL. Omit `<app_name>` for a top-level view.

Follows HTMX conventions — supports full-page, HTMX partial, and form-based
(create/edit) patterns. Writes the view, creates the template using the design
system, wires the URL, and writes tests covering the happy path, HTMX partial
path, and auth branches. Generates a `<model>Form` in `forms.py` if the view is
form-based and one does not already exist.

Examples:
  /dj-create-view store product_list    # app-level view
  /dj-create-view dashboard             # top-level view
