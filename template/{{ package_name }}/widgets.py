from django.forms.widgets import FileInput
from django.utils.html import format_html
from django.utils.translation import gettext as _


class ThumbnailWidget(FileInput):
    """File input widget that renders a sorl thumbnail preview."""

    def __init__(self, *args, **kwargs):
        self.image = kwargs.pop("image", None)
        super().__init__(*args, **kwargs)
        self.attrs.setdefault("class", "file-input")

    def render(self, name, value, attrs=None, renderer=None):
        file_input = super().render(name, value, attrs, renderer)
        preview = self._render_preview()
        return format_html(
            '<div x-data="{{ previewUrl: null }}"'
            ' @change="previewUrl = $event.target.files[0]'
            " ? URL.createObjectURL($event.target.files[0]) : null\">"
            "{}{}</div>",
            preview,
            file_input,
        )

    def _render_preview(self):
        if self.image:
            from sorl.thumbnail import get_thumbnail

            im = get_thumbnail(self.image, "340x240", crop="center")
            return format_html(
                '<img src="{url}" :src="previewUrl ?? \'{url}\'"'
                ' alt="{alt}" width="{w}" height="{h}" class="mb-2 rounded-lg" />',
                url=im.url,
                alt=_("Preview"),
                w=im.width,
                h=im.height,
            )
        return format_html(
            "<template x-if=\"previewUrl\">"
            '<img :src="previewUrl" alt="{}" width="340" height="240"'
            ' class="mb-2 rounded-lg" />'
            "</template>",
            _("Preview"),
        )
