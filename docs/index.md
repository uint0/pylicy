# Welcome to Pylicy

Pylicy is an customizable and extensible policy creation and enforcement framework written in python.

Pylicy aims to allow users to define policies in code, describe policy application rules in configuration, and handle policy application within the framework.


## Installation

```shell
$ pip install pylicy
```

## A Simple Example

```python
import asyncio
import pylicy

@pylicy.policy_checker('token_age_policy')
async def my_policy(resource: pylicy.Resource, rule: pylicy.Rule):
    if resource.data['token_age'] > 30:
        return pylicy.PolicyDecision(
            action=pylicy.PolicyDecisionAction.DENY,
            reason="expired",
            detail={'age': resource.data['token_age']}
        )
    elif resource.data['token_age'] > 20:
        return pylicy.PolicyDecision(action=pylicy.PolicyDecisionAction.WARN)
    else:
        return pylicy.PolicyDecision(action=pylicy.PolicyDecisionAction.ALLOW)

policies = pylicy.Pylicy.from_rules([
    pylicy.UserRule(
        name='token_age',
        resources=['*_token*'],
        policies=['token_*'],
    )
])  # or pylicy.Pylicy.from_yaml("/path/to/rules.yml")

results = asyncio.run(policies.apply_all([
    pylicy.Resource(id='my_ok_token', data={'token_age': 10}),
    pylicy.Resource(id='my_old_token', data={'token_age': 21}),
    pylicy.Resource(id='my_expired_token', data={'token_age': 90})
]))

print(results)
```

## License

This project is licensed under the terms of the MIT license.