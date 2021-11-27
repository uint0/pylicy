.PHONY: list

list:
	@LC_ALL=C $(MAKE) -pRrq -f $(lastword $(MAKEFILE_LIST)) : 2>/dev/null | awk -v RS= -F: '/^# File/,/^# Finished Make data base/ {if ($$1 !~ "^[#.]") {print $$1}}' | sort | egrep -v -e '^[^[:alnum:]]' -e '^$@$$'

setup:
	poetry install

check: lint test

test: utest

utest:
	poetry run pytest --cov-report term-missing --cov=pylicy tests/

lint:
	poetry run mypy pylicy/ tests/
	poetry run flake8 pylicy/ tests/
	poetry run black --check pylicy/ tests/
	poetry run isort --check-only pylicy/ tests/

format:
	poetry run black pylicy/ tests/
	poetry run isort pylicy/ tests/

build:
	poetry build

publish: build
	poetry publish