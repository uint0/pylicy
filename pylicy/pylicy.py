import asyncio
import itertools
import json
import logging
from typing import IO, AnyStr, Dict, List, NamedTuple, Optional, Union

import yaml

from . import policy
from . import rules as rules_
from . import utils
from .models import JSON, PolicyChecker, PolicyDecision, Resource, Rule, UserRule


class ExecutionPlanStep(NamedTuple):
    policy_name: str
    rule: Rule

    def __repr__(self) -> str:  # pragma: no cover
        return f"{self.rule.name}:{self.policy_name}"


ExecutionPlan = List[ExecutionPlanStep]


class Pylicy:
    def __init__(
        self,
        rules: List[Rule],
        *,
        scope: str = policy.DEFAULT_POLICY_SCOPE,
        logger: Optional[logging.Logger] = None,
    ):
        self._scope = scope
        self._policies = policy.get_policies(scope)
        self._rules = rules.copy()

        self._logger = logger or logging.getLogger(__name__)

    @property
    def rules(self) -> List[Rule]:
        return self._rules.copy()

    @property
    def policies(self) -> Dict[str, PolicyChecker]:
        return self._policies.copy()

    @property
    def _weighted_rules(self) -> Dict[int, List[Rule]]:
        """Group and sort rules by weight whilst preserving order"""
        return dict(
            sorted(
                [
                    (weight, list(group))
                    for weight, group in itertools.groupby(self._rules, lambda rule: rule.weight)
                ],
                key=lambda w: w[0],
            )
        )

    async def apply(self, resource: Resource) -> Dict[str, PolicyDecision]:
        """Applies relevant policy to a resource

        Args:
            resource: Resource to apply policies to

        Returns:
            A mapping of policy names to policy decisions

        Raises:
            TypeError: when resource isn't a Resource
        """

        if not isinstance(resource, Resource):
            raise TypeError("resource should be a pylicy.Resource type")

        plan = self._resolve_resource_policies(resource.id)
        self._logger.debug("Processing resource '%s' with plan %s", resource.id, plan)
        return dict(
            zip(
                [step.policy_name for step in plan],
                await asyncio.gather(
                    *[self._execute_policy(step.policy_name, resource, step.rule) for step in plan]
                ),
            )
        )

    async def apply_all(self, resources: List[Resource]) -> Dict[str, Dict[str, PolicyDecision]]:
        """Applies all policies to a list of resources

        Args:
            resources: resources to apply policies to

        Returns:
            A list of resource -> {policy_name -> policy_decision} mappings

        Raises:
            TypeError: when resource isn't a list
        """

        if not isinstance(resources, list):
            raise TypeError(
                "Did not get expected list of resources - use .apply(resource) for singular resources"
            )

        return dict(
            zip(
                [resource.id for resource in resources],
                await asyncio.gather(*[self.apply(resource) for resource in resources]),
            )
        )

    def __eq__(self, other: object) -> bool:
        """Checks if objects are equal"""
        if not isinstance(other, Pylicy):
            return False
        return all(
            [
                other._scope == self._scope,
                other._policies == self._policies,
                other._rules == self._rules,
            ]
        )

    def __repr__(self) -> str:  # pragma: nocover
        return (
            "<Pylicy "
            + f"rules=[{','.join([rule.name for rule in self._rules])}] "
            + f"policies=[{','.join([policy for policy in self._policies])}]>"
        )

    def _resolve_resource_policies(self, resource: str) -> ExecutionPlan:
        """Plans policies and rules to use, considering weight"""
        policy_names = list(self._policies.keys())

        effective_rules = self._find_effective_rules_for_resource(resource)
        if len(effective_rules) == 0:
            return []

        plan: ExecutionPlan = []
        seen: set[str] = set()

        for rule in reversed(effective_rules):
            rule_policies = utils.match_patterns(rule.policy_patterns, policy_names)
            plan.extend(
                [
                    ExecutionPlanStep(policy_name=p_name, rule=rule)
                    for p_name in rule_policies.include
                    if p_name not in seen
                ]
            )
            seen.update(rule_policies.matched)

        return plan

    def _find_effective_rules_for_resource(self, resource: str) -> List[Rule]:
        """Finds all rules applicable to a given resource, ordered by non-decreasing weight"""
        effective_rules: List[Rule] = []
        for rule_list in self._weighted_rules.values():
            for rule in rule_list:
                matches = utils.match_patterns(rule.resource_patterns, [resource])
                if len(matches.include) > 0:
                    effective_rules.append(rule)
        return effective_rules

    async def _execute_policy(self, policy_name: str, resource: Resource, rule: Rule) -> PolicyDecision:
        """Executes a policy given its name"""
        self._logger.debug(
            "Executing policy %s (from %s) for resource %s", policy_name, rule.name, resource.id
        )
        return await self._policies[policy_name](resource, rule)

    # === Factories === #

    @classmethod
    def from_raw_dict(
        cls, raw_dict: Dict[str, JSON], *, scope: str = policy.DEFAULT_POLICY_SCOPE
    ) -> "Pylicy":
        """Loads a Pylicy object from a raw mapping

        Args:
            raw_dict: Raw mapping to load (of the form {version: 1, rules: {}})
            scope: policy scope to load for

        Returns:
            A Pylicy object created from the configuration
        """
        return cls(rules_.load(raw_dict, policy.get_policies(scope)), scope=scope)

    @classmethod
    def from_yaml(
        cls, file: Union[str, IO[AnyStr]], *, scope: str = policy.DEFAULT_POLICY_SCOPE
    ) -> "Pylicy":
        """Loads a Pylicy object from a yaml file on disk

        Args:
            file: File handle or path to yaml file to load
            scope: policy scope to load for

        Returns:
            A Pylicy object created from the configuration
        """
        if isinstance(file, str):
            with open(file, "r") as f:
                return cls.from_raw_dict(yaml.safe_load(f), scope=scope)
        else:
            return cls.from_raw_dict(yaml.safe_load(file), scope=scope)

    @classmethod
    def from_json(
        cls, file: Union[str, IO[AnyStr]], *, scope: str = policy.DEFAULT_POLICY_SCOPE
    ) -> "Pylicy":
        """Loads a Pylicy object from a json file on disk

        Args:
            file: File handle or path to json file to load
            scope: policy scope to load for

        Returns:
            A Pylicy object created from the configuration
        """
        if isinstance(file, str):
            with open(file, "r") as f:
                return cls.from_raw_dict(json.load(f), scope=scope)
        else:
            return cls.from_raw_dict(json.load(file), scope=scope)

    @classmethod
    def from_rules(
        cls, rules: List[Union[Rule, UserRule]], *, scope: str = policy.DEFAULT_POLICY_SCOPE
    ) -> "Pylicy":
        """Loads a Pylicy object directly from a list of rules

        Args:
            rules: List of pylicy rules
            scope: policy scope to load for

        Returns:
            A Pylicy object created from the configuration
        """

        policies = policy.get_policies(scope)
        concrete_rules: List[Rule] = [
            (rule if isinstance(rule, Rule) else rules_.resolve_user_rule(rule, policies)) for rule in rules
        ]
        return cls(concrete_rules, scope=scope)
