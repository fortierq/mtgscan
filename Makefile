SHELL := /bin/bash

test:
	set -o allexport; \
	source azure.env; \
	set +o allexport; \
	poetry run python tests/test.py

example:
	set -o allexport; \
	source azure.env; \
	set +o allexport; \
	poetry run python example.py
