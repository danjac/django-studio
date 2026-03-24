**/dj-create-app <app_name>**

Scaffolds a new Django app with the standard project structure.

Creates `apps.py`, `models.py`, `views.py`, `urls.py`, `admin.py`, and a `tests/`
directory. Registers the app in `settings.py`, wires it into `config/urls.py`,
and adds its fixtures to `conftest.py`.

Example:
  /dj-create-app orders
