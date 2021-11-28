import io

import pytest

import pylicy


@pytest.mark.asyncio
async def test_getting_started_example() -> None:
    scope = "test_getting_started_example"

    @pylicy.policy_checker("token_rotation", scope=scope)
    async def token_rotation_policy(resource: pylicy.Resource, rule: pylicy.Rule) -> pylicy.PolicyDecision:
        if resource.data["age"] > 30:
            return pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.DENY,
                reason="too old",
            )
        else:
            return pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.ALLOW,
            )

    token_metadata = [
        {"name": "my_token", "token": {"age": 10}},
        {"name": "my_old_token", "token": {"age": 60}},
        {"name": "longlived_a", "token": {"age": 60}},
        {"name": "longlived_b", "token": {"age": 60}},
        {"name": "alices_token", "token": {"age": 60}},
    ]

    pylicy_resources = [pylicy.Resource(id=token["name"], data=token["token"]) for token in token_metadata]

    policies = pylicy.Pylicy.from_yaml(
        io.StringIO(
            """
    version: 1

    rules:
      - name: token_rotation_all
        description: Enforce the token rotation policy for all resources
        resources: '*'
        policies: token_rotation
      - name: special_longlived_tokens
        description: Exclude certain tokens from this rule
        resources:
          - longlived_*
          - alices_token
        policies: '!token_rotation'
    """
        ),
        scope=scope,
    )

    decisions = await policies.apply_all(pylicy_resources)

    assert decisions == {
        "alices_token": {},
        "longlived_a": {},
        "longlived_b": {},
        "my_old_token": {
            "token_rotation": pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.DENY, reason="too old", detail=None
            )
        },
        "my_token": {
            "token_rotation": pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.ALLOW, reason=None, detail=None
            )
        },
    }
