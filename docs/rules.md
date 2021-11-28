# Rules

Rules are pylicy's way of associating resources to policies. They support wildcard matching and exclusion, and implement a weight
system to allow for overrides and specificity. pylicy supports definition of these rules either in configuration (yaml or json) or
in code.

## Rule Types

### User Rules

User rules implement a interface with sensible defaults to allow users to easily write rules. YAML and JSON rule defintions only
support user rules and pylicy exports the `pylicy.UserRule` model to allow for user rules to be defined in code.

??? abstract "Schema"
     - **`name`**: A short string identifying the rule. (required)
     - **`description`**: A longer description and summary of the rule. (optional: defaults to `name`)
     - **`weight`**: A weight for the rule. Rules with higher weights are prioritized. (optional: defaults to 100)
     - **`resources`**: A wildcard pattern or list of such patterns used to match resource names. (required)
     - **`policies`**: A wildcard pattern or list of such patterns used to match policy names. (required)
     - **`context`**: Any additional context to pass to policy checkers. This is useful for resource-specific configurations (optional)


**Example**

=== "YAML"

    ```yaml
    version: 1

    rules:
      - name: my_barebones_rule
        resources: '*'
        policies: '*'
      
      - name: my_cool_rule
        description: My cool rule!
        weight: 200
        resources: 'wildcard_*_pattern'
        policies:
          - 'a_list_of_*'
          - 'policy_names_?'
          - '!not_this'
        context:
          cool: true
    ```

=== "JSON"

    ```json
    {
      "version": 1,
      "rules": [
        {
          "name": "my_barebones_rule",
          "resources": "*",
          "policies": "*"
        },
        {
          "name": "my_cool_rule",
          "description": "My cool rule!",
          "weight": 200,
          "resources": "wildcard_*_pattern",
          "policies": [
            "a_list_of_*",
            "policy_names_?",
            "!not_this"
          ],
          "context": {
            "cool": true
          }
        }
      ]
    }
    ```

=== "Python"

    ```python
    [
      pylicy.UserRule(
        name="my_barebones_rule",
        resources="*",
        policies="*"
      ),
      pylicy.UserRule(
        name="my_cool_rule",
        description="My cool rule!",
        weight=200,
        resources="wildcard_*_pattern",
        policies=[
          "a_list_of_*",
          "policy_names_?",
          "!not_this"
        ],
        context={
          "cool": true
        }
      )
    ]
    ```

### "Concrete" Rules

Concrete Rules (or just `Rule`) are pylicy's internal representation of a rule and are what is passed to your policy checkers.
pylicy will happily accept these from code. They largely follow the same schema as user rules but disallow any optional types or fields.

??? abstract "Schema"
     - **`name`**: Same as user rule. (required)
     - **`description`**: Same as user rule. (required)
     - **`weight`**: Same as user rule. (required)
     - **`resource_patterns`**: A list of wildcard patterns used to match resource names. (required)
     - **`policy_patterns`**: A list of wildcard patterns used to match policy names. (required)
     - **`context`**: Same as user rule.

**Example**

```python
pylicy.Rule(
    name='my_concrete_rule',
    description='Nothing is optional',
    weight=100,
    resource_patterns=['*'],
    policy_petterns=['*'],
    context=None,
)
```

## Rule Semantics

### Patterns
pylicy internally uses python's [`fnmatch`](https://docs.python.org/3/library/fnmatch.html) module with some extension
to perform matching and hence supports all patterns used by that module. In addition to fnmatch's patterns pylicy
also supports a leading `!` for negation.

??? Example
     - `[ij] is a good variable name` matches both `i is a good variable name` and `j is a good variable name`
     - `hello *` matches `hello world` but not `world hello`
     - `?phone` matches `iphone` and `jphone` but not `apple phone`
     - `!*script` matches `python` but not `javascript` or `typescript`

When a list of patterns is specified they are resolved first to last (from low indexes to high indexes). pylicy will reduce
the matches for every pattern and only apply a new pattern to the this list of reduced matches .This has implications on
what is matched by a list of patterns containing negations.

??? Example
    Assuming we have the set `[iphone, ipad, iwatch, apple watch]`.

      - `i*, !*watch, apple watch` will match `iphone, ipad, apple watch`
      - `i*, apple watch, !*watch` will match only `iphone, ipad`


### Conflicts
Rules are designed to permit conflicts (e.g. one rule may match `my_policy` whilst another may match `!my_policy`).
This is perfectly legal and even desirable to introduce special cases for certain resources. pylicy will perform the
following actions to decide what rules to match.

1. Rules of higher weight are preferred over lower weights.
2. Policies excluded by a rule of higher weight will override policies included by rules of lower weight.
3. Rules defined later in order (of a higher index) will be preferred over rules of lower index within the same weight class.
4. Contexts will be populated by only the first matching rule.

??? Example
    For the rules
    ```yaml
    version: 1

    rules:
      - name: enforce_all
          description: Enforce all policies for all resources
          weight: 1
          resources: '*'
          policies: '*'
      - name: allow_admin_wildcards
          description: Allow admins to have wildcards
          resources: admin_*
          policies:
          - '!token_no_wildcard'
      - name: frank_extend_time
          description: Frank can have longer times betwen token rotation
          resources: frank_*
          policies:
          - token_age
          context:
            max_rotation_time: 365
    ```

    - For the resource `dummy_token` only the `enforce_all` rule would apply.
    - For the resource `frank_token` the `token_age` policy and context would come from `frank_extend_time` and all other policies from `enforce_all`.
    - For the resource `admin_token` the `token_no_wildcard` policy would not apply, all other policies would come from `enforce_all`.



