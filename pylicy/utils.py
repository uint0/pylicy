import fnmatch
import operator
from collections.abc import Iterable, Iterator
from typing import List, Optional, TypeVar, Union

T = TypeVar("T")


class PatternMatches:
    """Represents a result of a match_patterns operation"""

    def __init__(self, include: set[str], matched: set[str], *, all: Optional[List[str]] = None):
        self._include = include
        self._matched = matched
        self._all = all

    @property
    def include(self) -> List[str]:
        return self._set_to_list(self._include)

    @property
    def exclude(self) -> List[str]:
        return self._set_to_list(self._matched - self._include)

    @property
    def matched(self) -> List[str]:
        return self._set_to_list(self._matched)

    def _set_to_list(self, s: set[str]) -> List[str]:
        return [e for e in self._all if e in s] if self._all is not None else list(s)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, PatternMatches)
            and other.include == self.include
            and other.exclude == self.exclude
        )

    def __contains__(self, key: str) -> bool:
        return key in self._include

    def __repr__(self) -> str:  # pragma: nocover
        return repr(self.include)

    def __iter__(self) -> Iterator[str]:
        return iter(self.include)


def ensure_list(item: Union[List[T], T]) -> List[T]:
    """Ensure that a item is a list, converting it if it isn't already

    Args:
        item: Potentially list item to check and convert

    Returns:
        item if item is already a list otherwise [item]

    Notes:
        - Iterables and other "list-like" items will also be wrapped in a list
        - The original reference is returned if the input is already a list

    Example:
    >>> ensure_list([1, 2, 3, 4])
    [1, 2, 3, 4]
    >>> ensure_list(5)
    [5]
    >>> a_list = [1, 2, 3, 4]
    >>> ensure_list(a_list) is a_list
    True
    >>> ensure_list({1: 2})
    [{1: 2}]
    """
    return item if isinstance(item, list) else [item]


def match_patterns(patterns: Iterable[str], items: Iterable[str]) -> PatternMatches:
    """Match a list of strings against a list of patterns returning all matches

    Args:
        patterns: A list of patterns to match
        items: A list of strings to match against

    Returns:
        a list of strings matching all patterns

    Notes:
        Patterns should be standard fnmatch patterns, however patterns can be prefixed with
        `!` in order to exclude that pattern.
        Patterns are evaluated in order.

    Example:
        >>> match_patterns(["simple1*", "simple2*"], ["simple1aa", "simple2bb", "complex"])
        ["simple1aa", "simple2bb"]
        >>> match_patterns(["i*", "!*watch"], ["iphone", "ipad", "iwatch", "apple watch"])
        ["iphone", "ipad"]
        >>> match_patterns(["i*", "!*watch", "apple watch"], ["iphone", "ipad", "iwatch", "apple watch"])
        ["iphone", "ipad", "apple watch"]
        >>> match_patterns(["i*", "apple watch", "!*watch"], ["iphone", "ipad", "iwatch", "apple watch"])
        ["iphone", "ipad"]
    """
    patterns = list(patterns)
    if len(patterns) == 0:
        return PatternMatches(set(), set())

    def is_negative(s: str) -> bool:
        return s.startswith("!")

    all_items = list(items)
    seen_set = set()
    working_set = set(all_items) if is_negative(patterns[0]) else set()
    for pattern in patterns:
        resolver_operator = operator.or_
        if is_negative(pattern):
            pattern = pattern[1:]
            resolver_operator = operator.sub

        operation_set = set(fnmatch.filter(items, pattern))
        seen_set |= operation_set
        working_set = resolver_operator(working_set, operation_set)

    return PatternMatches(working_set, working_set | seen_set, all=all_items)
