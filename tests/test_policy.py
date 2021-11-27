from typing import Any

import pytest

from pylicy import models, policy


async def stub_checker(resource: models.Resource, rule: models.Rule) -> models.PolicyDecision:
    return models.PolicyDecision(action=models.PolicyDecisionAction.ALLOW)


def test_get_policies_non_existent() -> None:
    with pytest.raises(KeyError):
        policy.get_policies(scope="non-existent")


def test_get_policies_always_has_default() -> None:
    policy.get_policies()


def test_get_policies_returns_copy() -> None:
    scope = "test_get_policies_returns_copy"

    policy.register_policy("my_policy", stub_checker, scope=scope)

    policies = policy.get_policies(scope=scope)
    policies["canary"] = stub_checker
    assert "canary" not in policy.get_policies(scope=scope)


def test_register_policy_to_scope() -> None:
    scope = "test_register_policy_to_scope"

    policy.register_policy("my_policy", stub_checker, scope=scope)

    assert policy.get_policies(scope=scope) == {"my_policy": stub_checker}


def test_register_policy_duplicate_warning() -> None:
    scope = "test_register_policy_duplicate"

    policy.register_policy("my_policy", stub_checker, scope=scope)

    with pytest.raises(RuntimeWarning):
        policy.register_policy("my_policy", stub_checker, scope=scope)


def test_register_policy_uncallable() -> None:
    scope = "test_register_policy_uncallable"

    with pytest.raises(TypeError):
        policy.register_policy("my_policy", "uncallable", scope=scope)  # type: ignore


def test_register_policy_non_coroutine() -> None:
    scope = "test_register_policy_non_coroutine"

    with pytest.raises(RuntimeWarning):
        policy.register_policy("my_policy", lambda rsrc, rule: None, scope=scope)  # type: ignore


def test_register_policy_decorator() -> None:
    scope = "test_register_policy_decorator"

    @policy.policy_checker("my_policy", scope=scope)
    async def checker(_1: Any, __2: Any) -> Any:
        pass

    assert policy.get_policies(scope=scope) == {"my_policy": checker}


def test_register_policy_decorator_used_directly_error() -> None:
    with pytest.raises(TypeError):

        @policy.policy_checker  # type: ignore
        async def checker(_1: Any, __2: Any) -> Any:
            pass


def test_policy_class_auto_register() -> None:
    scope = "test_policy_class_auto_register"

    class MyPolicy(policy.Policy, scope=scope):
        name = "my_policy"

        async def __call__(self, _1: Any, __2: Any) -> Any:
            pass

    policies = policy.get_policies(scope=scope)
    assert "my_policy" in policies
    assert isinstance(policies["my_policy"], MyPolicy)


def test_policy_class_unnamed() -> None:
    scope = "test_policy_class_unnamed"

    with pytest.raises(TypeError):

        class MyPolicy(policy.Policy, scope=scope):
            async def __call__(self, _1: Any, __2: Any) -> Any:
                pass


def test_policy_class_ignores_abstract_registration() -> None:
    scope = "test_policy_class_ignores_abstract_registration"

    class MyPolicy(policy.Policy, scope=scope):
        pass

    class ConcretePolicy(MyPolicy, scope=scope):
        name = "my_policy"

        async def __call__(self, _1: Any, __2: Any) -> Any:
            pass

    policies = policy.get_policies(scope=scope)
    assert "my_policy" in policies
    assert isinstance(policies["my_policy"], ConcretePolicy)


def test_policy_class_disallow_incomplete_registration() -> None:
    scope = "test_policy_class_disallow_incomplete_registration"

    with pytest.raises(TypeError):

        class MyPolicy(policy.Policy, scope=scope):
            name = "my_policy"
