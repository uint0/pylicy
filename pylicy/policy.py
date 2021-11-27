import abc
import collections
import inspect
from collections.abc import Callable
from typing import Dict

from .models import PolicyChecker, PolicyDecision, Resource, Rule

DEFAULT_POLICY_SCOPE = "default"


policies: Dict[str, Dict[str, PolicyChecker]] = collections.defaultdict(dict)
policies[DEFAULT_POLICY_SCOPE] = {}


def get_policies(scope: str = DEFAULT_POLICY_SCOPE) -> Dict[str, PolicyChecker]:
    """Gets a list of policies

    Args:
        scope: The scope or namespace of policies to fetch

    Returns:
        Policies associated with the scope

    Raises:
        KeyError: when the scope is not known
    """

    if scope not in policies:
        raise KeyError(f"Unknown scope {scope}")

    return policies[scope].copy()


def register_policy(name: str, policy: PolicyChecker, *, scope: str = DEFAULT_POLICY_SCOPE) -> None:
    """Registers a policy

    Args:
        name: Name of the policy
        policy: The policy callable to register
        scope: The scope or namespace the policy should be registered into

    Raises:
        RuntimeWarning: Upon a conflicting duplicate class registration
        TypeError: When the policy is malformed
    """
    if not callable(policy):
        raise TypeError("Cannot register a non-callable as a policy")
    if name in policies.get(scope, []):  # Do not touch a scope in-case something else goes wrong later
        raise RuntimeWarning(f"Policy {name} has already been registered to scope {scope}, ignoring")

    if not isinstance(policy, BasePolicy) and not inspect.iscoroutinefunction(policy):
        raise RuntimeWarning(
            f"Cannot register synchronus checker for policy {name} - use a coroutine function instead"
        )

    policies[scope][name] = policy


def policy_checker(
    policy_name: str, *, scope: str = DEFAULT_POLICY_SCOPE
) -> Callable[[PolicyChecker], PolicyChecker]:
    """A function decorator to register a function under a name

    Arg:
        fn: Function to decorate
        policy_name: Name of the policy
        scope: The scope or namespace the policy should be registered into

    Returns:
        A decorator to wrap a function

    Example:
    >>> @policy_checker("my_policy", scope="docstr_example")
    ... async def my_check(_1, __2):
    ...     pass
    """

    if callable(policy_name):
        raise TypeError("policy decorator should be called (i.e. @policy('name'))")

    def decorator(fn: PolicyChecker) -> PolicyChecker:
        register_policy(policy_name, fn, scope=scope)
        return fn

    return decorator


class BasePolicy(abc.ABC):
    """Abstract base policy class defining common interfaces for policies"""

    name: str

    @abc.abstractmethod
    async def __call__(self, resource: Resource, rule: Rule) -> PolicyDecision:
        """Perform checks and to ensure a resource complies with the policy

        Args:
            resource: A resource object containing the name and descriptor
            rule: The rule being applied

        Returns:
            Detailed decision object to be audit logged. See PolicyDecision for detailed explaination
        """


class Policy(BasePolicy):
    """Base policy class which automatically registers policies"""

    def __init_subclass__(cls, *, scope: str = DEFAULT_POLICY_SCOPE) -> None:
        """Registration hook for concrete subclasses

        Args:
            Scope: Optional advanced scoping for grouping policies

        Raises:
            TypeError: When a subclass is named but still abstract
        """
        # Everything that provides a name must no longer be abstract
        if hasattr(cls, "name") and inspect.isabstract(cls):
            raise TypeError(f"Named policy {cls.name} cannot be abstract")

        if inspect.isabstract(cls):
            return

        if not hasattr(cls, "name"):
            raise TypeError(
                f"Cannot instantiate abstract class {cls.__name__} without abstract attribute name"
            )

        register_policy(cls.name, cls(), scope=scope)
