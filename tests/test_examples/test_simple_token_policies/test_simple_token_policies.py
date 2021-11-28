import datetime as dt
import json
import os.path
from typing import Any, Dict, List

import pytest

import pylicy

TEST_DIR = os.path.dirname(__file__)


@pytest.mark.asyncio
async def test_simple_token_policies_example() -> None:
    scope = "test_simple_token_policies_example"

    def mock_get_resources() -> List[Dict[str, Any]]:
        return json.load(open(os.path.join(TEST_DIR, "mock_api_tokens.json")))  # type: ignore

    def mock_get_datetime() -> dt.datetime:
        return dt.datetime(year=2021, month=12, day=2, hour=0, minute=0)

    class TokenAgePolicy(pylicy.Policy, scope=scope):
        """Checks that a token is < 30 days since last rotation"""

        name = "token_age"

        async def __call__(self, resource: pylicy.Resource, rule: pylicy.Rule) -> pylicy.PolicyDecision:
            rule_context = rule.context or {}
            assert isinstance(rule_context, dict)
            max_rotation_time = rule_context.get("max_rotation_time", 30)
            warn_rotation_time = rule_context.get("warn_rotation_time", int(0.8 * max_rotation_time))

            time_since_rotation = mock_get_datetime() - dt.datetime.fromisoformat(
                resource.data["rotated_at"]
            )

            if time_since_rotation > dt.timedelta(days=max_rotation_time):
                return pylicy.PolicyDecision(
                    action=pylicy.PolicyDecisionAction.DENY,
                    reason=f"Token has exceeded required timeframe for rotation ({max_rotation_time} days)",
                    detail={"time_since_rotation": time_since_rotation.days},
                )
            elif time_since_rotation > dt.timedelta(days=warn_rotation_time):
                return pylicy.PolicyDecision(
                    action=pylicy.PolicyDecisionAction.WARN,
                    reason="Token needs to be rotated soon",
                    detail={"time_since_rotation": time_since_rotation.days},
                )
            else:
                return pylicy.PolicyDecision(
                    action=pylicy.PolicyDecisionAction.ALLOW,
                    reason="Token has been rotated recently",
                    detail={"time_since_rotation": time_since_rotation.days},
                )

    class TokenNoWildcardPolicy(pylicy.Policy, scope=scope):
        """Checks that token does not have wildcard perms"""

        name = "token_no_wildcard"

        async def __call__(self, resource: pylicy.Resource, rule: pylicy.Rule) -> pylicy.PolicyDecision:
            invalid_policies = [scope for scope in resource.data["scopes"] if "*" in scope]

            if invalid_policies:
                return pylicy.PolicyDecision(
                    action=pylicy.PolicyDecisionAction.DENY,
                    reason="One or more policies has a wildcard",
                    detail={"wildcard_policies": invalid_policies},
                )
            else:
                return pylicy.PolicyDecision(action=pylicy.PolicyDecisionAction.ALLOW)

    policies = pylicy.Pylicy.from_yaml(os.path.join(TEST_DIR, "./rules.yml"), scope=scope)
    resources = mock_get_resources()
    result = await policies.apply_all(
        [pylicy.Resource(id=rsrc["name"], data=rsrc["token"]) for rsrc in resources]
    )
    print(result)
    assert result == {
        "alice_token": {
            "token_age": pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.ALLOW,
                reason="Token has been rotated recently",
                detail={"time_since_rotation": 17},
            ),
            "token_no_wildcard": pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.ALLOW,
            ),
        },
        "bob_token": {
            "token_age": pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.ALLOW,
                reason="Token has been rotated recently",
                detail={"time_since_rotation": 17},
            ),
            "token_no_wildcard": pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.DENY,
                reason="One or more policies has a wildcard",
                detail={"wildcard_policies": ["*"]},
            ),
        },
        "david_token": {
            "token_age": pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.DENY,
                reason="Token has exceeded required timeframe for rotation (30 days)",
                detail={"time_since_rotation": 184},
            ),
            "token_no_wildcard": pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.ALLOW,
            ),
        },
        "eve_token": {
            "token_age": pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.DENY,
                reason="Token has exceeded required timeframe for rotation (30 days)",
                detail={"time_since_rotation": 215},
            ),
            "token_no_wildcard": pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.DENY,
                reason="One or more policies has a wildcard",
                detail={"wildcard_policies": ["pets:*"]},
            ),
        },
        "frank_token": {
            "token_age": pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.ALLOW,
                reason="Token has been rotated recently",
                detail={"time_since_rotation": 184},
            ),
            "token_no_wildcard": pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.ALLOW,
            ),
        },
        "admin_pets_token": {
            "token_age": pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.DENY,
                reason="Token has exceeded required timeframe for rotation (30 days)",
                detail={"time_since_rotation": 215},
            )
        },
    }
