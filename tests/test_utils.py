import itertools
from collections.abc import Iterable
from typing import Any, List

from hypothesis import given
from hypothesis import strategies as st

from pylicy import utils


@given(st.lists(st.integers()))
def test_ensure_list_does_not_wrapt_existing_list(ls: List[Any]) -> None:
    assert utils.ensure_list(ls) == ls
    assert utils.ensure_list(ls) is ls


@given(st.integers())
def test_ensure_list_wraps_non_lists(val: int) -> None:
    assert utils.ensure_list(val) == [val]


@given(st.iterables(st.integers()))
def test_ensure_list_wraps_iterable(it: Iterable[int]) -> None:
    assert utils.ensure_list(it) == [it]


@given(st.iterables(st.text()), st.iterables(st.text()))
def test_match_patterns_matches_hypo(pattern: Iterable[str], text: Iterable[str]) -> None:
    pattern_items, pattern = itertools.tee(pattern)
    text_items, text = itertools.tee(text)
    res = utils.match_patterns(pattern, text)
    assert all(r in text_items for r in res)
    assert utils.match_patterns(pattern_items, res) == res


def test_match_patterns_matches() -> None:
    assert utils.match_patterns(
        ["simple1*", "simple2*"], ["simple1aa", "simple2bb", "complex"]
    ) == utils.PatternMatches(
        {"simple1aa", "simple2bb"},
        {"simple1aa", "simple2bb"},
        all=["simple1aa", "simple2bb", "complex"],
    )
    assert utils.match_patterns(
        ["i*", "!*watch"], ["iphone", "ipad", "iwatch", "apple watch"]
    ) == utils.PatternMatches(
        {"iphone", "ipad"},
        {"iphone", "ipad", "iwatch", "apple watch"},
        all=["iphone", "ipad", "iwatch", "apple watch"],
    )
    assert utils.match_patterns(
        ["i*", "!*watch", "apple watch"], ["iphone", "ipad", "iwatch", "apple watch"]
    ) == utils.PatternMatches(
        {"iphone", "ipad", "apple watch"},
        {"iphone", "ipad", "iwatch", "apple watch"},
        all=["iphone", "ipad", "iwatch", "apple watch"],
    )
    assert utils.match_patterns(
        ["i*", "apple watch", "!*watch"], ["iphone", "ipad", "iwatch", "apple watch"]
    ) == utils.PatternMatches(
        {
            "iphone",
            "ipad",
        },
        {"iphone", "ipad", "iwatch", "apple watch"},
        all=["iphone", "ipad", "iwatch", "apple watch"],
    )


def test_pattern_matches_props() -> None:
    assert "in" in utils.PatternMatches({"in"}, {"in", "out"})
    assert "out" not in utils.PatternMatches({"in"}, {"in", "out"})
    assert utils.PatternMatches({"in"}, {"in", "out"}, all=["in", "out"]).matched == ["in", "out"]
    assert utils.PatternMatches({"in"}, {"in", "out"}, all=["in", "out"]).include == ["in"]
    assert utils.PatternMatches({"in"}, {"in", "out"}, all=["in", "out"]).exclude == ["out"]
