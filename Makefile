.PHONY: help run test lint format format-check lock-check secret-scan \
	docker-build docker-build-dev docker-run docker-stop docker-shell \
	install-hooks

IMAGE_NAME := avocadodash
CONTAINER_NAME := avocadodash
GITLEAKS_IMAGE := zricethezav/gitleaks:latest
PORT := 8050

help: ## Muestra esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

## --- Desarrollo (recomendado): código en el host, app corriendo en Docker con hot-reload ---

run: ## Levanta la app en Docker con hot-reload (http://localhost:8050). Requiere `make docker-build` antes
	docker run --rm -it -p $(PORT):$(PORT) \
		-v "$(CURDIR)":/app \
		-e DEBUG=true \
		--name $(CONTAINER_NAME)-dev \
		$(IMAGE_NAME):latest \
		poetry run python src/app.py

## --- Tests y lint: corren dentro de Docker con la imagen de dev (pytest/ruff) ---

test: ## Ejecuta la suite de tests dentro de Docker. Requiere `make docker-build-dev` antes
	docker run --rm -v "$(CURDIR)":/app $(IMAGE_NAME):dev poetry run pytest

lint: ## Corre ruff check dentro de Docker. Requiere `make docker-build-dev` antes
	docker run --rm -v "$(CURDIR)":/app $(IMAGE_NAME):dev poetry run ruff check .

format: ## Formatea el código con ruff format dentro de Docker. Requiere `make docker-build-dev` antes
	docker run --rm -v "$(CURDIR)":/app $(IMAGE_NAME):dev poetry run ruff format .

format-check: ## Verifica el formato sin modificar archivos, dentro de Docker. Requiere `make docker-build-dev` antes
	docker run --rm -v "$(CURDIR)":/app $(IMAGE_NAME):dev poetry run ruff format --check .

lock-check: ## Verifica que poetry.lock esté sincronizado con pyproject.toml. Requiere `make docker-build-dev` antes
	docker run --rm -v "$(CURDIR)":/app $(IMAGE_NAME):dev poetry check --lock

secret-scan: ## Escanea el diff staged en busca de secretos con gitleaks (usa el índice de git, no todo el repo)
	docker run --rm -v "$(CURDIR)":/repo -w /repo $(GITLEAKS_IMAGE) protect --staged -v --source /repo

## --- Docker (build de las imágenes) ---

docker-build: ## Construye la imagen Docker de producción
	docker build -t $(IMAGE_NAME):latest .

docker-build-dev: ## Construye la imagen Docker de desarrollo (incluye pytest y ruff)
	docker build --target dev -t $(IMAGE_NAME):dev .

docker-run: ## Levanta la app dentro de un contenedor Docker (imagen de producción, sin hot-reload)
	docker run --rm -p $(PORT):$(PORT) --name $(CONTAINER_NAME) $(IMAGE_NAME):latest

docker-stop: ## Detiene los contenedores en ejecución (producción y dev)
	-docker stop $(CONTAINER_NAME) $(CONTAINER_NAME)-dev

docker-shell: ## Abre una shell dentro de la imagen Docker de producción
	docker run --rm -it --entrypoint /bin/bash $(IMAGE_NAME):latest

## --- Git hooks ---

install-hooks: ## Habilita los git hooks del repo (lint en pre-commit)
	git config core.hooksPath .githooks
	chmod +x .githooks/*
