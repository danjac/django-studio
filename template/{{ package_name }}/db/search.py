import functools
import operator
from typing import TypeVar, cast

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Q, QuerySet

_QS = TypeVar("_QS", bound=QuerySet)


def search(
    qs: _QS,
    value: str,
    *search_fields: str,
    annotation: str = "rank",
    config: str = "simple",
    search_type: str = "websearch",
) -> _QS:
    """Search a queryset using PostgreSQL full-text search.

    Args:
        qs: The queryset to search.
        value: The search query string.
        search_fields: tsvector fields to search. Defaults to ``("search_vector",)``.
        annotation: Name for the rank annotation.
        config: PostgreSQL text search configuration.
        search_type: Type of search query (websearch, plain, phrase, raw).
    """
    if not value:
        return qs.none()

    fields = search_fields or ("search_vector",)
    query = SearchQuery(value, search_type=search_type, config=config)

    rank = functools.reduce(
        operator.add,  # pyright: ignore[reportArgumentType]
        (SearchRank(F(field), query=query) for field in fields),
    )

    q = functools.reduce(
        operator.or_,
        (Q(**{field: query}) for field in fields),
    )

    return cast("_QS", qs.annotate(**{annotation: rank}).filter(q))
