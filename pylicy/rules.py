from collections.abc import Iterable
from typing import Dict, List

from pydantic import ValidationError

from . import utils
from .models import JSON, Rule, UserRule


def resolve_user_rule(user_rule: UserRule, policy_names: Iterable[str]) -> Rule:
    """Resolves optional fields on a UserRule to produce a concrete Rule

    Args:
        user_rule: UserRule to resolve
        policy_names: Names of the policies to use during rule resolution

    Returns:
        Concrete Rule
    """

    return Rule(
        name=user_rule.name,
        description=user_rule.description if user_rule.description is not None else user_rule.name,
        weight=user_rule.weight,
        resource_patterns=utils.ensure_list(user_rule.resources),
        policy_patterns=utils.ensure_list(user_rule.policies),
        context=user_rule.context,
    )


def load_v1(rules: Dict[str, JSON], policy_names: Iterable[str]) -> List[Rule]:
    """Loads human-friendly rules using the v1 layout"""

    if "rules" not in rules:
        raise AttributeError("`rules` list not found in rules")
    if not isinstance(rules["rules"], list):
        raise TypeError("`rules` should be a list of rules")

    raw_rules: Iterable[JSON] = rules["rules"]
    user_rules: List[UserRule] = []
    for i, rule in enumerate(raw_rules):
        if not isinstance(rule, dict):
            raise TypeError(f"`rule` {i} should be a dict")

        try:
            user_rules.append(UserRule(**rule))
        except ValidationError as e:
            raise ValueError(f'Invalid rule {rule.get("name", f"<anonymous rule {i}>")}') from e

    return [resolve_user_rule(rule, policy_names) for rule in user_rules]


def load(rules: Dict[str, JSON], policy_names: Iterable[str]) -> List[Rule]:
    """Loads human-friendly rules into a internal representation

    Args:
        rules: User defined list of rules

    Returns:
        List of internal rule representations

    Raises:
        AttributeError: when a version is missing
        NotImplementedError: when the major version is not supported
    """

    if "version" not in rules:
        raise AttributeError("`version` not found in rules")

    major_version = str(rules["version"]).split(".")[0]

    if major_version == "1":
        return load_v1(rules, policy_names)
    else:
        raise NotImplementedError(f"Unsupported major version {major_version}")
