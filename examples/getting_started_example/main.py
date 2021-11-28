import asyncio
import pprint

import pylicy

@pylicy.policy_checker('token_rotation')
async def token_rotation_policy(resource, rule):
    if resource.data['age'] > 30:
        return pylicy.PolicyDecision(
            action=pylicy.PolicyDecisionAction.DENY,
            reason="too old",
        )
    else:
        return pylicy.PolicyDecision(
            action=pylicy.PolicyDecisionAction.ALLOW,
        )

def get_all_token_metadata():
    return [
        {'name': 'my_token',     'token': {'age': 10}},
        {'name': 'my_old_token', 'token': {'age': 60}},
        {'name': 'longlived_a',  'token': {'age': 60}},
        {'name': 'longlived_b',  'token': {'age': 60}},
        {'name': 'alices_token', 'token': {'age': 60}},
    ]

pylicy_resources = [
    pylicy.Resource(id=token['name'], data=token['token'])
    for token in get_all_token_metadata()
]

policies = pylicy.Pylicy.from_yaml('./rules.yml')
decisions = asyncio.run(policies.apply_all(pylicy_resources))

pprint.pprint(decisions)
