**/dj-create-crud <app_name> <model_name>**

Generates a complete set of CRUD views for a model: list, detail, create, edit,
delete.

Includes `forms.py`, templates (following the design system), URLs, and full test
coverage. Runs `/dj-create-app` or `/dj-create-model` first if the app or model
does not exist yet.

Example:
  /dj-create-crud store Product
