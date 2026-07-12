.PHONY: help install run test lint format format-check \
	docker-build docker-run docker-stop docker-shell \
	install-hooks

IMAGE_NAME := avocadodash
CONTAINER_NAME := avocadodash
PORT := 8050

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

## --- Desarrollo local (fuera del contenedor, vía Poetry) ---

install: ## Instala las dependencias con Poetry
	poetry install

run: ## Levanta la app fuera del contenedor (http://localhost:8050)
	poetry run python src/app.py

test: ## Ejecuta la suite de tests fuera del contenedor
	poetry run pytest

lint: ## Corre ruff check sobre el código
	poetry run ruff check .

format: ## Formatea el código con ruff format
	poetry run ruff format .

format-check: ## Verifica el formato sin modificar archivos
	poetry run ruff format --check .

## --- Docker (build/run de la imagen de producción) ---

docker-build: ## Construye la imagen Docker
	docker build -t $(IMAGE_NAME):latest .

docker-run: ## Levanta la app dentro de un contenedor Docker
	docker run --rm -p $(PORT):$(PORT) --name $(CONTAINER_NAME) $(IMAGE_NAME):latest

docker-stop: ## Detiene el contenedor en ejecución
	docker stop $(CONTAINER_NAME)

docker-shell: ## Abre una shell dentro de la imagen Docker
	docker run --rm -it --entrypoint /bin/bash $(IMAGE_NAME):latest

## --- Git hooks ---

install-hooks: ## Habilita los git hooks del repo (lint en pre-commit)
	git config core.hooksPath .githooks
	chmod +x .githooks/*
