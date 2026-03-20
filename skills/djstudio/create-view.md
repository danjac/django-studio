Add a view, template, and URL following HTMX conventions.

## Required reading

- `docs/HTMX.md`
- `docs/Tailwind.md`

**Parsing arguments:**

- Two words (e.g. `create-view store product_list`): first is `<app_name>`, second is `<view_name>`.
- One word (e.g. `create-view index`): no app — this is a top-level view.

**Top-level vs app-level** affects three things: where the view function lives,
where the template goes, and where the URL is wired.

| | App-level | Top-level |
|---|---|---|
| View file | `<package_name>/<app_name>/views.py` | `<package_name>/views.py` |
| Template | `templates/<app_name>/<view_name>.html` | `templates/<view_name>.html` |
| URL file | `<package_name>/<app_name>/urls.py` | `config/urls.py` |
| Test file | `<package_name>/<app_name>/tests/test_views.py` | `<package_name>/tests/test_views.py` |

---

**Steps:**

1. **Choose the response pattern:**

   Always add an explicit HTTP method decorator (see `docs/Views.md`).

   Full page (read-only):
   ```python
   from django.contrib.auth.decorators import login_required
   from django.template.response import TemplateResponse
   from django.views.decorators.http import require_safe

   from <package_name>.http.request import HttpRequest

   @require_safe
   @login_required
   def <view_name>(request: HttpRequest) -> TemplateResponse:
       return TemplateResponse(request, "<template_path>", {})
   ```

   With an HTMX-swappable partial (e.g. a list that refreshes inline):
   ```python
   from <package_name>.http.request import HttpRequest
   from <package_name>.partials import render_partial_response
   from django.template.response import TemplateResponse

   def <view_name>(request: HttpRequest) -> TemplateResponse:
       return render_partial_response(
           request,
           "<template_path>",
           context={},
           target="<htmx-target-id>",
           partial="<partial-block-name>",
       )
   ```

   `render_partial_response` renders the full template on first load and
   switches to the named partial block when `HX-Target` matches `target`.

   Form-based view (create / edit):
   ```python
   from django.contrib import messages
   from django.http import HttpResponseRedirect
   from django.shortcuts import redirect
   from django.urls import reverse
   from django.utils.translation import gettext as _

   from <package_name>.http.decorators import require_form_methods
   from <package_name>.http.request import HttpRequest
   from <package_name>.partials import render_partial_response
   from <app_name>.forms import <model_name>Form  # create if it doesn't exist

   @login_required
   @require_form_methods
   def <view_name>(request: HttpRequest) -> TemplateResponse | HttpResponseRedirect:
       if request.method == "POST":
           form = <model_name>Form(request.POST)
           if form.is_valid():
               form.save()
               messages.success(request, _("Saved."))
               return redirect(reverse("<app_name>:<success_view>"))
       else:
           form = <model_name>Form()
       return render_partial_response(
           request,
           "<template_path>",
           {"form": form},
           target="<form-id>",
           partial="<form-id>",
       )
   ```

   If a `<model_name>Form` does not yet exist in `<app_name>/forms.py`, create it:
   ```python
   from django import forms
   from <package_name>.<app_name>.models import <model_name>

   class <model_name>Form(forms.ModelForm):
       class Meta:
           model = <model_name>
           fields: list[str] = []  # fill in required fields
   ```

2. **Create the template** at the path from the table above.
   For HTMX partials, use Django 6 named partial blocks. Use DaisyUI classes for all components.

3. **Wire the URL** in the file from the table above:
   ```python
   path("<path>/", views.<view_name>, name="<view_name>"),
   ```
   For top-level views, import from `<package_name>.views`, not an app module.

4. **Write tests** — minimum:
   - Happy path
   - HTMX partial path (headers `HX-Request: true`, `HX-Target: <target-id>`)
   - Any auth/permission branch
   100% coverage is required.

5. Verify: `just check-all`

---

## Help

**djstudio create-view [<app_name>] <view_name>**

Adds a view function, template, and URL. Omit `<app_name>` for a top-level view.

Follows HTMX conventions — supports full-page, HTMX partial, and form-based (create/edit) patterns. Writes the view, creates the template using the design system, wires the URL, and writes tests covering the happy path, HTMX partial path, and auth branches. Generates a `<model>Form` in `forms.py` if the view is form-based and one does not already exist.

Examples:
  /djstudio create-view store product_list    # app-level view
  /djstudio create-view dashboard             # top-level view
