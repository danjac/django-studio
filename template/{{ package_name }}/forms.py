from django.forms.renderers import TemplatesSetting


class FormRenderer(TemplatesSetting):
    """Renders each form field with `templates/forms/field.html`."""

    field_template_name = "forms/field.html"
