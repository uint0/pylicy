# Pylicy

An customizable and extensible policy creation and enforcement framework.

## Installation

```
$ pip install pylicy
```

## A Simple Example

Examples can be found in the `examples/` directory.

```python
import asyncio
import pylicy

@pylicy.policy_checker('token_age_policy')
async def my_policy(resource: pylicy.Resource, rule: pylicy.Rule) -> pylicy.PolicyDecision:
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
])

results = asyncio.run(policies.apply_all([
    pylicy.Resource(id='my_ok_token', data={'token_age': 10}),
    pylicy.Resource(id='my_old_token', data={'token_age': 21}),
    pylicy.Resource(id='my_expired_token', data={'token_age': 90})
]))

print(results)
```

## License
This project is licensed under the terms of the MIT license.
