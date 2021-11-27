import pytest

from pylicy import (
    PolicyDecision,
    PolicyDecisionAction,
    Pylicy,
    Resource,
    Rule,
    UserRule,
    policy,
)


@pytest.mark.asyncio
async def test_pylicy_apply_no_resource_matches() -> None:
    policies = Pylicy.from_rules(
        [UserRule(name="simple_rule", resources=["do_not_match_*"], policies=["not_used"])]
    )
    assert await policies.apply(Resource(id="my_resource")) == {}


@pytest.mark.asyncio
async def test_pylicy_apply_bad_resource_type() -> None:
    policies = Pylicy.from_rules(
        [UserRule(name="simple_rule", resources=["do_not_match_*"], policies=["not_used"])]
    )
    with pytest.raises(TypeError):
        await policies.apply("not a resource")  # type: ignore


@pytest.mark.asyncio
async def test_pylicy_apply_no_policy_match() -> None:
    policies = Pylicy.from_rules(
        [UserRule(name="simple_rule", resources=["my_resource"], policies=["no_such_policy"])]
    )
    assert await policies.apply(Resource(id="my_resource")) == {}


@pytest.mark.asyncio
async def test_pylicy_apply_match() -> None:
    scope = "test_pylicy_apply_match"

    async def checker(rsrc: Resource, rule: Rule) -> PolicyDecision:
        return PolicyDecision(action=PolicyDecisionAction.ALLOW)

    policy.register_policy("my_policy", checker, scope=scope)
    policies = Pylicy.from_rules(
        [UserRule(name="simple_rule", resources=["my_resource"], policies=["my_policy"])], scope=scope
    )
    assert await policies.apply(Resource(id="my_resource")) == {
        "my_policy": PolicyDecision(action=PolicyDecisionAction.ALLOW)
    }


@pytest.mark.asyncio
async def test_pylicy_apply_all_no_resource_matches() -> None:
    policies = Pylicy.from_rules(
        [UserRule(name="simple_rule", resources=["do_not_match_*"], policies=["not_used"])]
    )
    assert await policies.apply_all([Resource(id="my_resource"), Resource(id="my_other_resource")]) == {
        "my_resource": {},
        "my_other_resource": {},
    }


@pytest.mark.asyncio
async def test_pylicy_apply_all_bad_resource_list_type() -> None:
    policies = Pylicy.from_rules(
        [UserRule(name="simple_rule", resources=["do_not_match_*"], policies=["not_used"])]
    )
    with pytest.raises(TypeError):
        await policies.apply_all("Not a resource list")  # type: ignore


@pytest.mark.asyncio
async def test_pylicy_apply_all_match() -> None:
    scope = "test_pylicy_apply_all_match"

    async def checker(rsrc: Resource, rule: Rule) -> PolicyDecision:
        return PolicyDecision(action=PolicyDecisionAction.ALLOW)

    policy.register_policy("my_policy", checker, scope=scope)
    policies = Pylicy.from_rules(
        [
            UserRule(name="simple_rule", resources=["my_resource"], policies=["my_policy"]),
            UserRule(name="simple_rule", resources=["my_other_resource"], policies=["my_policy"]),
        ],
        scope=scope,
    )
    assert await policies.apply_all([Resource(id="my_resource"), Resource(id="my_other_resource")]) == {
        "my_resource": {"my_policy": PolicyDecision(action=PolicyDecisionAction.ALLOW)},
        "my_other_resource": {"my_policy": PolicyDecision(action=PolicyDecisionAction.ALLOW)},
    }
