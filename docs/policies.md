# Policies

Policies are constructs used by pylicy to allow users to define rules they are expected to be async callable and need to be
named and registered with pylicy before use.

## Policy scopes

Policies are grouped by scope. You can optionally declare your desired scope when registering your policy checker or otherwise
pylicy will automatically place your policy into the `default` scope. Each `Pylicy` object will only process policies for a given
scope. This allows you to split up unrelated policies.

??? Example
    ```python
    @pylicy.policy_checker('my_policy', scope='scope1')
    async def my_policy_in_scope_1(resource, rule):
        ...

    @pylicy.policy_checker('my_policy', scope='scope2')
    async def my_policy_in_scope_2(resource, rule):
        ...
    
    # This will only run my_policy_in_scope_1
    pylicy.Pylicy.from_rules([
        pylicy.UserRule(name='my_rule', resources='*', policies='my_policy')
    ], scope='scope1').apply(...)
    ```

## Policy Signature

Policies are expected to take in 2 parameters referencing the resource and rule and return a policy decision. A simple
policy signature looks something like the following.

```python
@pylicy.policy_checker('my_policy')
async def my_policy(
    resource: pylicy.Resource,
    rule: pylicy.Rule,
) -> pylicy.PolicyDecision:
    return pylicy.PolicyDecision(
        action=pylicy.PolicyDecisionAction.ALLOW,
        reason="everything is allowed!",
        details={'some_structured': 'details'},
    )
```

## Policy registration

Policies need to be named and registered with pylicy so they can be detected before use. pylicy supports 3 methods for doing this.

### Policy decorators

So far in examples we have been using the `@pylicy.policy_checker` decorator to register our checkers. This is the primary
way of registering policies to pylicy. This takes in a required policy name and a optional scope parameter and will automatically
register your checker under that name and scope.

```python
@pylicy.policy_checker('my_policy', scope='some_scope')
async def my_policy(resource, rule):
    ...
```

### Policy class

pylicy additionally exports an abstract `Policy` base class. Subclass will be automatically registered to pylicy based on their
name attribute. `Policy` classes are expected to implemented the same signature as described above on their `__call__` function.
Policies declared this way should only declare a `name` if they are concrete, and will only be registered if they declare a `name`.

```python
class MyPolicy(Policy, scope='my_scope'):
    name ='my_policy'

    async def __call__(resource, rule):
        return pylicy.PolicyDecision(...)
```

??? Tip
    This inheritance behaviour allows for additional configurability.
    ```python
    from abc import abstractmethod

    class AuditingPolicy(Policy):
        async def __call__(resource, rule):
            decision = await self.check(resource, rule)
            audit_logger.log(decision)
            return decision
        
        @abstractmethod
        async def check(resource, rule):
            ...

    class MyPolicy(AuditingPolicy):
        name = 'my_policy'

        async def check(resource, rule):
            return PolicyDecision(...)
    ```

### Additional policy helpers

#### BasePolicy class

pylicy also exports a `BasePolicy` class which performs much the same role as `Policy` but does not perform any registration
or validation behaviour. There is generally no need to use this class.

#### Manual registration

pylicy also allows manual registration of any async callable using the `pylicy.register_policy` method.

```python
async def my_policy(resource, rule):
    ...
pylicy.register_policy('my_policy', my_policy, scope='scope')
```
