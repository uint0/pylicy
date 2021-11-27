# Developing

## Setting up
`make setup`

pylicy uses [poetry](https://python-poetry.org/) for package managements. Installation instructions can be found on their website.

To setup you can run `poetry install` or `make setup`.


## Testing
`make test`

pylicy uses pytest for test running and reporting. As well as a combination of normal unit-tests and [hypothesis](https://hypothesis.readthedocs.io/en/latest/index.html) tests for writing tests.

Tests should be put into `tests/` and can be run with `poetry run pytest tests/` or `make test`.


## Code style
`make lint`, `make format`

pylicy uses a combination of `black`, `isort`, and `flake8` for linting and `mypy` for type-checking.
Code can be auto-formatted with `make format` and linted with `make lint`.

Any function should be documented with doc-strings using [google's docstring guidelines](https://google.github.io/styleguide/pyguide.html).


## Deploying
