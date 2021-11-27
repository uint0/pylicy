import enum
from collections.abc import Awaitable
from typing import Any, Callable, Dict, List, Optional, Union

from pydantic import BaseModel

# @ref https://github.com/python/typing/issues/182
JSON = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]


TRuleName = str
TResourceIdentifier = str


PolicyChecker = Callable[["Resource", "Rule"], Awaitable["PolicyDecision"]]


class PolicyDecisionAction(enum.Enum):
    """Action produced by policy enforcer

    Elements:
        ALLOW: Resource passes policy
        WARN: Resource passes policy but a warning should be raised
        DENY: Resource does not pass policy
    """

    ALLOW = "allow"
    WARN = "warn"
    DENY = "deny"


class PolicyDecision(BaseModel):
    """Decision produced by policy enforcer

    Fields:
        action: Policy action to take
        reason: Reason action was decided
        detail: Structured reason
    """

    action: PolicyDecisionAction
    reason: Optional[str] = None
    detail: Optional[JSON] = None


class Resource(BaseModel):
    """Thin wrapper for user resources to enforce an identifier

    Fields:
        id: Matchable string identifier for resource
        data: Resource data
    """

    id: TResourceIdentifier
    data: Any

    class Config:
        allow_mutation = False


class UserRule(BaseModel):
    """User Defined rule - will be processed to have sensible defaults

    Fields:
        name: Name of the rule
        description: Optional human-readable description
        weight: Optional weight of the rule - higher weights are prioritized
        resources: Pattern(s) to match resource ids to determine whether the rule should be applied
        policies: Pattern(s) to match policy names to be applied
        context: Any extra context
    """

    name: str
    description: Optional[str] = None
    weight: Optional[int] = 100
    resources: Union[str, List[str]]
    policies: Union[str, List[str]]
    context: Optional[JSON] = None


class Rule(BaseModel):
    """Concrete rule with no-nullable options

    Fields:
        name: Name of the rule
        description: Optional human-readable description
        weight: Optional weight of the rule - higher weights are prioritized
        resource_patterns: Pattern(s) to match resource ids to determine whether the rule should be applied
        policies: Pattern(s) to match policy names to be applied
        context: Any extra context
    """

    name: TRuleName
    description: str
    weight: int
    resource_patterns: List[TResourceIdentifier]
    policy_patterns: List[str]

    context: Optional[JSON] = None
