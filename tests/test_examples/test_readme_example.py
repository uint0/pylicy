import pytest

import pylicy


@pytest.mark.asyncio
async def test_readme_example() -> None:
    scope = "test_readme_example"

    @pylicy.policy_checker("token_age_policy", scope=scope)
    async def my_policy(resource: pylicy.Resource, rule: pylicy.Rule) -> pylicy.PolicyDecision:
        if resource.data["token_age"] > 30:
            return pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.DENY,
                reason="expired",
                detail={"age": resource.data["token_age"]},
            )
        elif resource.data["token_age"] > 20:
            return pylicy.PolicyDecision(action=pylicy.PolicyDecisionAction.WARN)
        else:
            return pylicy.PolicyDecision(action=pylicy.PolicyDecisionAction.ALLOW)

    policies = pylicy.Pylicy.from_rules(
        [
            pylicy.UserRule(
                name="token_age",
                resources=["*_token*"],
                policies=["token_*"],
            )
        ],
        scope=scope,
    )

    decisions = await policies.apply_all(
        [
            pylicy.Resource(id="my_ok_token", data={"token_age": 10}),
            pylicy.Resource(id="my_old_token", data={"token_age": 21}),
            pylicy.Resource(id="my_expired_token", data={"token_age": 90}),
        ]
    )

    assert decisions == {
        "my_ok_token": {
            "token_age_policy": pylicy.PolicyDecision(action=pylicy.PolicyDecisionAction.ALLOW)
        },
        "my_old_token": {
            "token_age_policy": pylicy.PolicyDecision(action=pylicy.PolicyDecisionAction.WARN)
        },
        "my_expired_token": {
            "token_age_policy": pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.DENY, reason="expired", detail={"age": 90}
            )
        },
    }
