Create a basic Django app with the standard file structure for this project.

**Steps:**

1. Create the directory structure under `<package_name>/<app_name>/`:

   ```
   __init__.py          (empty)
   apps.py
   models.py
   views.py
   urls.py
   admin.py
   tests/
       __init__.py      (empty)
       factories.py
       fixtures.py
       test_models.py
       test_views.py
   ```

   Do not create `forms.py`, `tasks.py`, or other files speculatively.

2. **apps.py**
   ```python
   from django.apps import AppConfig

   class <AppName>Config(AppConfig):
       default_auto_field = "django.db.models.BigAutoField"
       name = "<package_name>.<app_name>"
   ```

3. **models.py** — empty module, just `from __future__ import annotations`

4. **views.py** — typed request import only:
   ```python
   from __future__ import annotations
   from typing import TYPE_CHECKING

   if TYPE_CHECKING:
       from <package_name>.http.request import HttpRequest
   ```

5. **urls.py**
   ```python
   from __future__ import annotations
   from typing import TYPE_CHECKING

   if TYPE_CHECKING:
       from django.urls import URLPattern, URLResolver

   app_name = "<app_name>"
   urlpatterns: list[URLPattern | URLResolver] = []
   ```

6. **admin.py** — `from django.contrib import admin`

7. **tests/factories.py** — import stub only (no placeholder factories)

8. **tests/fixtures.py** — `import pytest` stub

9. **tests/test_models.py** and **tests/test_views.py** — `from __future__ import annotations`
   (empty stubs; coverage passes because source files are also empty)

10. Add to `config/settings.py` under `# Local apps`:
    ```python
    "<package_name>.<app_name>",
    ```

11. Add to `config/urls.py`:
    ```python
    path("<app_name>/", include("<package_name>.<app_name>.urls")),
    ```

12. Register fixtures in root `conftest.py`:
    ```python
    "<package_name>.<app_name>.tests.fixtures",
    ```

13. Verify: `just check-all`

---

## Help

**djstudio create-app <app_name>**

Scaffolds a new Django app with the standard project structure.

Creates `apps.py`, `models.py`, `views.py`, `urls.py`, `admin.py`, and a `tests/`
directory. Registers the app in `settings.py`, wires it into `config/urls.py`,
and adds its fixtures to `conftest.py`.

Example:
  /djstudio create-app orders
