# Getting Started

The pylicy workflow consists of writing policies, declaring rules, and then processing resources.

## Writing Policies

Policies are simple callables which take in a resource and rule and evaluate the to form some sort of decision.
This is documented further in the [Policies](../policies) page.

The following example policy will check if a given token resource is older than 30 days. If its too old the checker
will produce a `DENY` action, otherwise it will `ALLOW` it.
```python
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
```

## Declaring rules
[Rules](../rules) are then used to associate resources and policies. Resources are identified by their `id` and policies
by their `name`. Rules can be structured to overwrite amend prior rules for particular use-cases.

The following example ruleset will apply the `token_rotation_policy` to all resources except for `longlived_*` and `alices_token`.
```yaml
# rules.yml
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
```

## Fetching resources

Fetching resources is largely left up to the user, pylicy only requires some sort if identifier than can be used to match the resource.
Resources fetched should then be converted to `pylicy.Resource` objects which will then be passed to each policy.

```python
import pylicy

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
```


## Applying policies

Now that everything ready all thats left is to load our rules into pylicy and apply then to our resources!

In this case we will load our rules from before, and apply them to our `pylicy_resources` created above.
```python
import pylicy

policies = pylicy.Pylicy.from_yaml('./rules.yml')
decisions = await policies.apply_all(pylicy_resources)
```

Decisions will contain all the `PolicyDecision`s as produced by our policy checker functions grouped by resource then policy.

As you can see below the excluded rules were not run at all, whilst the two that did run had the policy applied successfully.
```python
decisions == {
    'alices_token': {},
    'longlived_a': {},
    'longlived_b': {},
    'my_old_token': {
        'token_rotation': PolicyDecision(
            action=PolicyDecisionAction.DENY, reason='too old', detail=None
        )
    },
    'my_token': {
        'token_rotation': PolicyDecision(
            action=PolicyDecisionAction.ALLOW, reason=None, detail=None
        )
    }
}
```

