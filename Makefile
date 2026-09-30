.PHONY: install install-dev run test lint format docker-build docker-run

install:
	python -m pip install -r requirements.txt

install-dev:
	python -m pip install -r requirements-dev.txt

run:
	python -m worker

test:
	pytest

lint:
	ruff check .
	ruff format --check .

format:
	ruff check --fix .
	ruff format .

docker-build:
	docker build -f docker/Dockerfile -t api-sfp-workers:local .

docker-run:
	docker run --rm --env-file .env -p 8081:8081 api-sfp-workers:local
