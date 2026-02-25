from collections.abc import Sequence
from typing import TYPE_CHECKING, TypeAlias, TypeVar

from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.db.models import Model, QuerySet
from django.utils.functional import cached_property

from {{cookiecutter.app_name}}.partials import render_partial_response

if TYPE_CHECKING:
    from django.template.response import TemplateResponse

    from {{cookiecutter.app_name}}.http.request import HttpRequest

T = TypeVar("T")
T_Model = TypeVar("T_Model", bound=Model)

ObjectList: TypeAlias = Sequence[T | T_Model] | QuerySet[T_Model]


def render_paginated_response(
    request: "HttpRequest",
    template_name: str,
    object_list: ObjectList,
    extra_context: dict | None = None,
    *,
    param: str = "page",
    target: str = "pagination",
    partial: str = "pagination",
    per_page: int = settings.DEFAULT_PAGE_SIZE,
) -> "TemplateResponse":
    """Render a paginated template response.

    Wraps ``render_partial_response`` with paginated context. Passes the
    ``Page`` object as ``page`` and honours the HTMX partial-swap pattern
    so only the list fragment is returned on subsequent page requests.

    Args:
        request: The current HTTP request.
        template_name: Template to render.
        object_list: Queryset or sequence to paginate.
        extra_context: Additional template context.
        param: Query-string parameter name for the page number.
        target: HTMX target element ID (used for partial rendering).
        partial: Named partial within the template.
        per_page: Page size (defaults to ``settings.DEFAULT_PAGE_SIZE``).
    """
    page = Paginator(object_list, per_page).get_page(request.GET.get(param, 1))

    return render_partial_response(
        request,
        template_name,
        {
            "page": page,
            "page_size": page.page_size,
            "pagination_target": target,
        }
        | (extra_context or {}),
        target=target,
        partial=partial,
    )


class Page:
    """Pagination page without COUNT(*) queries.

    See: https://testdriven.io/blog/django-avoid-counting/

    Object list access is lazy — no database query runs until the list is
    iterated or accessed.
    """

    def __init__(self, *, paginator: "Paginator", number: int) -> None:
        self.paginator = paginator
        self.page_size = paginator.per_page
        self.number = number

    def __repr__(self) -> str:
        """Return object representation."""
        return f"<Page {self.number}>"

    def __len__(self) -> int:
        """Return total number of items on this page."""
        return len(self.object_list)

    def __getitem__(self, index: int | slice) -> ObjectList:
        """Return item or slice from the object list."""
        return self.object_list[index]

    @cached_property
    def next_page_number(self) -> int:
        """Return the next page number, raising EmptyPage if none exists."""
        if self.has_next:
            return self.number + 1
        raise EmptyPage("Next page does not exist")

    @cached_property
    def previous_page_number(self) -> int:
        """Return the previous page number, raising EmptyPage if none exists."""
        if self.has_previous:
            return self.number - 1
        raise EmptyPage("Previous page does not exist")

    @cached_property
    def has_next(self) -> bool:
        """Return True if a next page exists."""
        return len(self.object_list_with_next_item) > self.page_size

    @cached_property
    def has_previous(self) -> bool:
        """Return True if a previous page exists."""
        return self.number > 1

    @cached_property
    def has_other_pages(self) -> bool:
        """Return True if any other pages exist."""
        return self.has_previous or self.has_next

    @cached_property
    def object_list(self) -> list:
        """Return the items for this page (without the lookahead item)."""
        return self.object_list_with_next_item[: self.page_size]

    @cached_property
    def object_list_with_next_item(self) -> list:
        """Return page items plus one extra to determine if a next page exists.

        Fetches ``per_page + 1`` items with LIMIT/OFFSET — no COUNT query.
        """
        start = (self.number - 1) * self.page_size
        end = start + self.page_size + 1
        return list(self.paginator.object_list[start:end])


class Paginator:
    """Paginator that avoids COUNT(*) queries."""

    def __init__(self, object_list: ObjectList, per_page: int) -> None:
        self.object_list = object_list
        self.per_page = per_page

    def get_page(self, number: int | str) -> Page:
        """Return a Page for the given number, defaulting to page 1 on error."""
        try:
            number = validate_page_number(number)
        except (PageNotAnInteger, EmptyPage):
            number = 1

        return Page(paginator=self, number=number)


def validate_page_number(number: int | str) -> int:
    """Validate and return the page number as a positive integer.

    Args:
        number: Raw page number (int or string from query params).

    Raises:
        PageNotAnInteger: If ``number`` cannot be coerced to an integer.
        EmptyPage: If ``number`` is less than 1.
    """
    try:
        number = int(number)
    except (TypeError, ValueError) as exc:
        raise PageNotAnInteger("Page number is not an integer") from exc
    if number < 1:
        raise EmptyPage("Page number is less than 1")
    return number
