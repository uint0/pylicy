import datetime as dt
import json

import pylicy


def mock_get_resources():
    return json.load(open('mock_api_tokens.json'))


def mock_get_datetime():
    return dt.datetime(year=2021, month=12, day=2, hour=0, minute=0)


class TokenAgePolicy(pylicy.Policy):
    """ Checks that a token is < 30 days since last rotation """
    name = 'token_age'

    async def __call__(self, resource, rule):
        rule_context = rule.context or {}
        max_rotation_time = rule_context.get('max_rotation_time', 30)
        warn_rotation_time = rule_context.get('warn_rotation_time', int(0.8 * max_rotation_time))

        time_since_rotation = mock_get_datetime() - dt.datetime.fromisoformat(resource.data['rotated_at'])

        if time_since_rotation > dt.timedelta(days=max_rotation_time):
            return pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.DENY,
                reason=f"Token has exceeded required timeframe for rotation ({max_rotation_time} days)",
                detail={'time_since_rotation': time_since_rotation.days},
            )
        elif time_since_rotation > dt.timedelta(days=warn_rotation_time):
            return pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.WARN,
                reason="Token needs to be rotated soon",
                detail={'time_since_rotation': time_since_rotation.days},
            )
        else:
            return pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.ALLOW,
                reason="Token has been rotated recently",
                detail={'time_since_rotation': time_since_rotation.days},
            )


class TokenNoWildcardPolicy(pylicy.Policy):
    """ Checks that token does not have wildcard perms """
    name = 'token_no_wildcard'

    async def __call__(self, resource, rule):
        invalid_policies = [scope for scope in resource.data['scopes'] if '*' in scope]

        if invalid_policies:
            return pylicy.PolicyDecision(
                action=pylicy.PolicyDecisionAction.DENY,
                reason="One or more policies has a wildcard",
                detail={'wildcard_policies': invalid_policies},
            )
        else:
            return pylicy.PolicyDecision(action=pylicy.PolicyDecisionAction.ALLOW)


if __name__ == '__main__':
    import asyncio
    import pprint
    policies = pylicy.Pylicy.from_yaml('./rules.yml')
    resources = mock_get_resources()
    result = asyncio.run(policies.apply_all([
        pylicy.Resource(id=rsrc['name'], data=rsrc['token']) for rsrc in resources
    ]))
    pprint.pprint(result)
