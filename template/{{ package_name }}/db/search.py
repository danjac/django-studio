import functools
import operator
from typing import TYPE_CHECKING, TypeAlias

from django.contrib.postgres.search import SearchQuery, SearchRank
from django.db.models import F, Q, QuerySet

if TYPE_CHECKING:
    Base: TypeAlias = QuerySet

else:
    Base = object


class Searchable(Base):
    """Mixin to add PostgreSQL full-text search capabilities to a QuerySet."""

    default_search_fields: tuple[str, ...] = ()

    def search(
        self,
        value: str,
        *search_fields: str,
        annotation: str = "rank",
        config: str = "simple",
        search_type: str = "websearch",
    ) -> QuerySet:
        """Search the queryset using PostgreSQL full-text search.

        Args:
            value: The search query string.
            search_fields: Fields to search. Falls back to default_search_fields.
            annotation: Name for the rank annotation.
            config: PostgreSQL text search configuration.
            search_type: Type of search query (websearch, plain, phrase, raw).
        """
        if not value:
            return self.none()

        search_fields = search_fields if search_fields else self.default_search_fields
        query = SearchQuery(value, search_type=search_type, config=config)

        rank = functools.reduce(
            lambda a, b: a + b,  # operator.add is overloaded; lambda avoids basedpyright error
            (SearchRank(F(field), query=query) for field in search_fields),
        )

        q = functools.reduce(
            operator.or_,
            (Q(**{field: query}) for field in search_fields),
        )

        return self.annotate(**{annotation: rank}).filter(q)
