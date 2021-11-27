import io
import json
from typing import Dict
from unittest import mock

import yaml

from pylicy import Pylicy, models

TEST_BASIC_USER_RAW_RULES: Dict[str, models.JSON] = {
    "version": 1,
    "rules": [
        {
            "name": "test_rule",
            "resources": ["test_resource_*"],
            "policies": ["test_policy_*"],
        }
    ],
}
TEST_BASIC_USER_RAW_RULES_PYLICY = Pylicy(
    [
        models.Rule(
            name="test_rule",
            description="test_rule",
            weight=100,
            resource_patterns=["test_resource_*"],
            policy_patterns=["test_policy_*"],
            context=None,
        )
    ]
)


def test_pylicy_load_raw_dict() -> None:
    assert Pylicy.from_raw_dict(TEST_BASIC_USER_RAW_RULES) == TEST_BASIC_USER_RAW_RULES_PYLICY


def test_pylicy_load_from_yaml_io() -> None:
    assert (
        Pylicy.from_yaml(io.StringIO(yaml.dump(TEST_BASIC_USER_RAW_RULES)))
        == TEST_BASIC_USER_RAW_RULES_PYLICY
    )


@mock.patch("builtins.open", new_callable=mock.mock_open, read_data=yaml.dump(TEST_BASIC_USER_RAW_RULES))
def test_pylicy_load_from_yaml_file_path(mock_open: mock.Mock) -> None:
    assert Pylicy.from_yaml("rules.yml") == TEST_BASIC_USER_RAW_RULES_PYLICY
    mock_open.assert_called_with("rules.yml", "r")


def test_pylicy_load_from_json_io() -> None:
    assert (
        Pylicy.from_json(io.StringIO(json.dumps(TEST_BASIC_USER_RAW_RULES)))
        == TEST_BASIC_USER_RAW_RULES_PYLICY
    )


@mock.patch("builtins.open", new_callable=mock.mock_open, read_data=json.dumps(TEST_BASIC_USER_RAW_RULES))
def test_pylicy_load_from_json_file_path(mock_open: mock.Mock) -> None:
    assert Pylicy.from_json("rules.json") == TEST_BASIC_USER_RAW_RULES_PYLICY
    mock_open.assert_called_with("rules.json", "r")


def test_pylicy_load_from_rules() -> None:
    assert (
        Pylicy.from_rules(
            [
                models.UserRule(
                    name="test_rule", resources=["test_resource_*"], policies=["test_policy_*"]
                ),
            ]
        )
        == TEST_BASIC_USER_RAW_RULES_PYLICY
    )
    assert (
        Pylicy.from_rules(
            [
                models.Rule(
                    name="test_rule",
                    description="test_rule",
                    weight=100,
                    resource_patterns=["test_resource_*"],
                    policy_patterns=["test_policy_*"],
                    context=None,
                ),
            ]
        )
        == TEST_BASIC_USER_RAW_RULES_PYLICY
    )
    assert Pylicy.from_rules(
        [
            models.Rule(
                name="test_concrete_rule",
                description="test_concrete_rule",
                weight=100,
                resource_patterns=["test_resource_*"],
                policy_patterns=["test_policy_*"],
                context=None,
            ),
            models.UserRule(name="test_rule", resources=["test_resource_*"], policies=["test_policy_*"]),
        ]
    ) == Pylicy(
        [
            models.Rule(
                name="test_concrete_rule",
                description="test_concrete_rule",
                weight=100,
                resource_patterns=["test_resource_*"],
                policy_patterns=["test_policy_*"],
                context=None,
            ),
            models.Rule(
                name="test_rule",
                description="test_rule",
                weight=100,
                resource_patterns=["test_resource_*"],
                policy_patterns=["test_policy_*"],
                context=None,
            ),
        ]
    )


def test_pylicy_rules_prop() -> None:
    expected_rules = [
        models.Rule(
            name="test_rule",
            description="test_rule",
            weight=100,
            resource_patterns=["test_resource_*"],
            policy_patterns=["test_policy_*"],
            context=None,
        ),
    ]
    assert TEST_BASIC_USER_RAW_RULES_PYLICY.rules == expected_rules

    rules_copy = TEST_BASIC_USER_RAW_RULES_PYLICY.rules.copy()
    rules_copy.append("canary")  # type: ignore
    assert TEST_BASIC_USER_RAW_RULES_PYLICY.rules == expected_rules
    assert TEST_BASIC_USER_RAW_RULES_PYLICY._rules == expected_rules


def test_pylicy_policies_prop() -> None:
    test_pylicy = Pylicy(
        [
            models.Rule(
                name="test_rule",
                description="test_rule",
                weight=100,
                resource_patterns=["test_resource_*"],
                policy_patterns=[],
                context=None,
            )
        ]
    )
    assert test_pylicy.policies == {}

    policies_copy = test_pylicy.policies
    policies_copy["canary"] = 1  # type: ignore
    assert test_pylicy.policies == {}
    assert test_pylicy._policies == {}


def test_pylicy_equality() -> None:
    test_rules = [
        models.Rule(
            name="test_rule",
            description="test_rule",
            weight=100,
            resource_patterns=["test_resource_*"],
            policy_patterns=[],
            context=None,
        ),
    ]
    assert TEST_BASIC_USER_RAW_RULES_PYLICY != {}
    assert TEST_BASIC_USER_RAW_RULES_PYLICY == TEST_BASIC_USER_RAW_RULES_PYLICY

    assert Pylicy(test_rules) is not Pylicy(test_rules)
    assert Pylicy(test_rules) == Pylicy(test_rules)

    assert Pylicy([]) != Pylicy(test_rules)
