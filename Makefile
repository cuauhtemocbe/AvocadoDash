.PHONY: help run test lint format format-check lock-check secret-scan typecheck validate clean \
	docker-build docker-build-dev docker-run docker-stop docker-shell \
	install-hooks

IMAGE_NAME := avocadodash
CONTAINER_NAME := avocadodash
GITLEAKS_IMAGE := zricethezav/gitleaks:latest
PORT := 8050
# Quality gates don't need network access; --network none also skips the
# per-container network setup, which is a noticeable share of startup time.
# Runs as the host user (not root) so the caches and reports written into the
# bind mount (.mypy_cache, .pytest_cache, .coverage, tests/coverage.xml) stay
# owned by you; HOME points at a writable dir because that uid has no passwd
# entry in the image.
DEV_RUN := docker run --rm --network none --user "$(shell id -u):$(shell id -g)" \
	-e HOME=/tmp -v "$(CURDIR)":/app $(IMAGE_NAME):dev

# Quality-gate commands, shared by the individual targets and by `validate` so
# the two can't drift apart. The dev image installs dependencies system-wide
# (`virtualenvs.create false`), so the tools are on PATH and `poetry run` is
# unnecessary — it only added ~5s of startup per invocation.
# The two mypy runs use different flags (strict on src, relaxed on tests) and
# therefore MUST keep separate cache dirs: sharing one makes each run
# invalidate the other's cache, re-checking everything (~20s each) every time
# instead of ~1s when warm. The caches live in the bind-mounted repo, so they
# persist across runs (`.mypy_cache/` is gitignored).
LINT_CMD := ruff check .
FORMAT_CHECK_CMD := ruff format --check .
TYPECHECK_CMD := mypy --strict src --cache-dir=.mypy_cache/src && \
	mypy tests --cache-dir=.mypy_cache/tests
TEST_CMD := pytest

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
	$(DEV_RUN) $(TEST_CMD)

lint: ## Corre ruff check dentro de Docker. Requiere `make docker-build-dev` antes
	$(DEV_RUN) $(LINT_CMD)

format: ## Formatea el código con ruff format dentro de Docker. Requiere `make docker-build-dev` antes
	$(DEV_RUN) ruff format .

format-check: ## Verifica el formato sin modificar archivos, dentro de Docker. Requiere `make docker-build-dev` antes
	$(DEV_RUN) $(FORMAT_CHECK_CMD)

lock-check: ## Verifica que poetry.lock esté sincronizado con pyproject.toml. Requiere `make docker-build-dev` antes
	$(DEV_RUN) poetry check --lock

secret-scan: ## Escanea el diff staged en busca de secretos con gitleaks (usa el índice de git, no todo el repo)
	docker run --rm -v "$(CURDIR)":/repo -w /repo $(GITLEAKS_IMAGE) protect --staged -v --source /repo

typecheck: ## Corre mypy --strict sobre src/ (relajado sobre tests/). Requiere `make docker-build-dev` antes
	$(DEV_RUN) sh -c '$(TYPECHECK_CMD)'

validate: ## Corre todos los quality gates (lint, format-check, typecheck, test) en un solo contenedor. Lo usa el pre-commit hook
	$(DEV_RUN) sh -c '$(LINT_CMD) && $(FORMAT_CHECK_CMD) && $(TYPECHECK_CMD) && $(TEST_CMD)'

clean: ## Borra cachés de mypy/pytest/ruff y reportes de cobertura (por si quedaron con dueño root de corridas anteriores)
	docker run --rm -v "$(CURDIR)":/app $(IMAGE_NAME):dev \
		rm -rf /app/.mypy_cache /app/.pytest_cache /app/.ruff_cache /app/.coverage /app/tests/coverage.xml

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
