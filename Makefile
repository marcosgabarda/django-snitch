# Common commands to habdle the project.
# ------------------------------------------------------------------------------
lint:
	poetry run isort . --profile black
	poetry run black .
	poetry run mypy .
