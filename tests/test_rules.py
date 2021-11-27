from typing import Any, Dict, List

import pytest
from hypothesis import given
from hypothesis import strategies as st

from pylicy import models, rules


def test_load_rules_bad_version() -> None:
    with pytest.raises(AttributeError):
        rules.load({}, [])
    with pytest.raises(NotImplementedError):
        rules.load({"version": 9999}, [])


@given(
    st.lists(
        st.fixed_dictionaries(
            {
                "name": st.text(),
                "weight": st.integers(),
                "resources": st.one_of(st.text(), st.lists(st.text())),
                "policies": st.one_of(st.text(), st.lists(st.text())),
                "description": st.one_of(st.none(), st.text()),
                "context": st.one_of(st.none(), st.dictionaries(st.text(), st.text())),
            }
        )
    ),
    st.lists(st.text()),
)
def test_load_v1_rules_correct_hypo(rule_set: List[Dict[str, Any]], policies: List[str]) -> None:
    loaded = rules.load({"version": 1, "rules": rule_set}, policies)
    assert all(isinstance(rule, models.Rule) for rule in loaded)


def test_load_v1_rules_correct() -> None:
    assert rules.load({"version": 1, "rules": []}, []) == []

    assert rules.load(
        {
            "version": 1,
            "rules": [
                {
                    "name": "enforce_all",
                    "weight": 1,
                    "resources": "*",
                    "policies": "*",
                },
                {
                    "name": "allow_admin_wildcards",
                    "description": "Allow admins to have wildcards",
                    "resources": "admin_*",
                    "policies": ["!token_no_wildcard"],
                },
                {
                    "name": "frank_extend_time",
                    "description": "Frank can have longer times betwen token rotation",
                    "resources": "frank_*",
                    "policies": ["token_age"],
                    "context": {"max_rotation_time": 365},
                },
            ],
        },
        ["token_age", "token_no_wildcard"],
    ) == [
        models.Rule(
            name="enforce_all",
            description="enforce_all",
            weight=1,
            resource_patterns=["*"],
            policy_patterns=["*"],
            context=None,
        ),
        models.Rule(
            name="allow_admin_wildcards",
            description="Allow admins to have wildcards",
            weight=100,
            resource_patterns=["admin_*"],
            policy_patterns=["!token_no_wildcard"],
            context=None,
        ),
        models.Rule(
            name="frank_extend_time",
            description="Frank can have longer times betwen token rotation",
            weight=100,
            resource_patterns=["frank_*"],
            policy_patterns=["token_age"],
            context={"max_rotation_time": 365},
        ),
    ]


def test_resolve_user_rules() -> None:
    assert rules.resolve_user_rule(
        models.UserRule(
            name="enforce_all",
            weight=1,
            resources="*",
            policies="*",
        ),
        ["token_age", "token_no_wildcard"],
    ) == models.Rule(
        name="enforce_all",
        description="enforce_all",
        weight=1,
        resource_patterns=["*"],
        policy_patterns=["*"],
        context=None,
    )
    assert rules.resolve_user_rule(
        models.UserRule(
            name="allow_admin_wildcards",
            description="Allow admins to have wildcards",
            resources="admin_*",
            policies=["!token_no_wildcard"],
        ),
        ["token_age", "token_no_wildcard"],
    ) == models.Rule(
        name="allow_admin_wildcards",
        description="Allow admins to have wildcards",
        weight=100,
        resource_patterns=["admin_*"],
        policy_patterns=["!token_no_wildcard"],
        context=None,
    )
    assert rules.resolve_user_rule(
        models.UserRule(
            name="frank_extend_time",
            description="Frank can have longer times betwen token rotation",
            resources="frank_*",
            policies=["token_age"],
            context={"max_rotation_time": 365},
        ),
        ["token_age", "token_no_wildcard"],
    ) == models.Rule(
        name="frank_extend_time",
        description="Frank can have longer times betwen token rotation",
        weight=100,
        resource_patterns=["frank_*"],
        policy_patterns=["token_age"],
        context={"max_rotation_time": 365},
    )


def test_load_v1_rules_no_rules() -> None:
    with pytest.raises(AttributeError):
        rules.load({"version": 1}, [])
    with pytest.raises(TypeError):
        rules.load({"version": 1, "rules": {}}, [])


def test_load_v1_rules_invalid_rule() -> None:
    with pytest.raises(TypeError):
        rules.load({"version": 1, "rules": ["hello"]}, [])
    with pytest.raises(ValueError):
        rules.load({"version": 1, "rules": [{}]}, [])
    with pytest.raises(ValueError):
        rules.load(
            {
                "version": 1,
                "rules": [
                    {
                        "name": "test",
                        "resources": [],
                        "policies": [],
                        "weight": "not a int",
                    }
                ],
            },
            [],
        )
