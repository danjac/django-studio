from django.forms.widgets import FileInput


class ThumbnailWidget(FileInput):
    """File input widget that renders a sorl thumbnail preview."""

    template_name = "django/forms/widgets/thumbnail_file_input.html"

    def __init__(self, *args, **kwargs):
        self.image = kwargs.pop("image", None)
        super().__init__(*args, **kwargs)
        self.attrs.setdefault("class", "file-input")

    def get_context(self, name, value, attrs):
        ctx = super().get_context(name, value, attrs)
        ctx["widget"]["image"] = self.image
        return ctx
