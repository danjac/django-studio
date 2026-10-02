import inspect

import pytest
from django import forms
from django.forms import widgets
from django.template.loader import get_template

# Widgets that render as a plain <input> through the "input" fallback partial.
_INPUT_FALLBACK = {
    widgets.ColorInput,
    widgets.EmailInput,
    widgets.NumberInput,
    widgets.SearchInput,
    widgets.TelInput,
    widgets.TextInput,
    widgets.URLInput,
}


def _visible_widgets() -> list[type[widgets.Widget]]:
    return [
        cls
        for cls in (getattr(widgets, name) for name in widgets.__all__)
        if inspect.isclass(cls)
        and issubclass(cls, widgets.Widget)
        and cls not in {widgets.Widget, widgets.MultiWidget, *_INPUT_FALLBACK}
        and not cls().is_hidden
    ]


class _Form(forms.Form):
    name = forms.CharField(help_text="Your full name")
    password = forms.CharField(widget=forms.PasswordInput)
    colour = forms.ChoiceField(
        choices=[("red", "Red"), ("blue", "Blue")],
        widget=forms.RadioSelect,
        help_text="Pick one",
    )


class TestWidgetPartials:
    @pytest.mark.parametrize("widget", _visible_widgets(), ids=lambda cls: cls.__name__)
    def test_widget_has_partial(self, widget):
        get_template(f"forms/partials.html#{widget.__name__.lower()}")


class TestFieldRendering:
    @pytest.fixture
    def form(self):
        form = _Form(data={})
        form.is_valid()
        return form

    def test_single_control_has_label(self, form):
        html = form["name"].as_field_group()
        assert '<label for="id_name"' in html
        assert "<legend" not in html

    def test_single_control_described_once(self, form):
        html = form["name"].as_field_group()
        assert html.count('aria-describedby="id_name_helptext id_name_error"') == 1
        assert '<ul id="id_name_error"' in html

    def test_grouped_widget_has_legend(self, form):
        html = form["colour"].as_field_group()
        assert "<legend" in html
        assert '<label for="id_colour"' not in html
        assert html.count('aria-describedby="id_colour_helptext id_colour_error"') == 1

    def test_password_toggle_is_focusable(self, form):
        html = form["password"].as_field_group()
        assert ':aria-pressed="show.toString()"' in html
        assert "tabindex" not in html
