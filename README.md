# 🥑 AvocadoDash

[![Python](https://img.shields.io/badge/Python-3.12.6-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Dash](https://img.shields.io/badge/Dash-3.2.0-00C7B7?logo=plotly&logoColor=white)](https://dash.plotly.com/)
[![Pandas](https://img.shields.io/badge/Pandas-2.3.2-150458?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Poetry](https://img.shields.io/badge/Poetry-deps-60A5FA?logo=poetry&logoColor=white)](https://python-poetry.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)
[![Railway](https://img.shields.io/badge/Deployed%20on-Railway-0B0D0E?logo=railway&logoColor=white)](https://railway.app/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Un tablero web interactivo para analizar **precios y ventas de aguacates en Estados Unidos (2015–2018)**.  
Construido con **Python Dash**, incluye múltiples tipos de visualizaciones para una exploración integral de los datos.

![AvocadoDash](./docs/AvocadoDash.png)

---

## 🚀 Características

- **📊 Gráficas de Series de Tiempo Interactivas** – Analiza tendencias de precios y volúmenes de ventas
- **🔍 Filtros Avanzados** – Filtra por región, tipo de aguacate (convencional/orgánico) y rango de fechas
- **📈 Análisis con Diagramas de Dispersión** – Explora relaciones entre variables con ejes configurables
- **📦 Gráficas de Caja (Boxplots)** – Compara distribuciones por tipo, región o año
- **🎨 Identidad Visual Propia** – Paleta, tipografía (Fraunces/Inter/IBM Plex Mono) y un ícono de marca inspirados en el corte transversal del aguacate mismo, no una plantilla genérica
- **📱 Diseño Responsivo** – Se adapta a pantallas angostas sin desbordes horizontales
- **⚡ Actualizaciones en Tiempo Real** – Todos los gráficos se actualizan dinámicamente según los filtros

---

## 🛠️ Tecnologías

- **Python 3.12.6** – Lenguaje principal  
- **Dash 3.2.0** – Framework para aplicaciones web con Python  
- **Pandas 2.3.2** – Manipulación y análisis de datos  
- **Plotly** – Librería de gráficos interactivos (integrada en Dash)  
- **Poetry** – Gestión de dependencias y empaquetado  
- **Docker** – Contenerización para despliegue sencillo  
- **Railway** – Plataforma de despliegue en la nube  

---

## 📁 Estructura del Proyecto
```
AvocadoDash/
├── src/
│   ├── app.py              # Aplicación principal de Dash
│   ├── avocado.csv         # Dataset (ventas de aguacate en EE.UU. 2015-2018)
│   ├── utils.py            # Funciones utilitarias
│   └── assets/
│       ├── favicon.ico     # Ícono del sitio
│       └── style.css       # Estilos CSS personalizados
├── tests/                  # Tests (pytest)
├── .githooks/              # Git hooks versionados (lint pre-commit)
├── Makefile                # Atajos para desarrollo, Docker y tests
├── Dockerfile              # Configuración del contenedor Docker
├── pyproject.toml          # Dependencias con Poetry
├── poetry.lock             # Versiones bloqueadas de dependencias
├── railway.json            # Configuración de Railway
└── README.md
```
---

## 🔧 Instalación y Configuración

### Opción 1: Docker con hot-reload (Recomendado)

Flujo recomendado para desarrollar: el código se edita en el host con tu
editor de siempre, pero la app corre dentro del contenedor y se recarga sola
al guardar, gracias al reloader integrado de Dash.

```bash
git clone https://github.com/cuauhtemocbe/AvocadoDash.git
cd AvocadoDash

make docker-build   # solo la primera vez o si cambian las dependencias
make run
```

Abrir en el navegador 👉 `http://localhost:8050`

---

### Opción 2: Usando Poetry (sin Docker)

```bash
# Clonar el repositorio
git clone https://github.com/cuauhtemocbe/AvocadoDash.git
cd AvocadoDash

# Instalar Poetry (si no está instalado)
curl -sSL https://install.python-poetry.org | python3 -

# Instalar dependencias
poetry install

# Ejecutar la aplicación
poetry run python src/app.py
```

Abrir en el navegador 👉 `http://localhost:8050`

---

### Opción 3: Docker sin hot-reload (imagen de producción)

```bash
git clone https://github.com/cuauhtemocbe/AvocadoDash.git
cd AvocadoDash

docker build -t avocado-dash .
docker run -p 8050:8050 avocado-dash

# equivalente con el Makefile:
make docker-build
make docker-run
```

---

## 🧰 Makefile

El proyecto incluye un `Makefile` con los comandos más comunes: el flujo de
desarrollo recomendado (`make run`, Docker con hot-reload), tests/lint
corriendo también dentro de Docker, y el build/run de las imágenes. Ver
todos los comandos disponibles con:

```bash
make help
```

| Comando              | Descripción                                                |
|----------------------|-------------------------------------------------------------|
| `make run`              | Levanta la app en Docker con hot-reload (`http://localhost:8050`). Requiere `make docker-build` antes |
| `make test`            | Ejecuta la suite de tests (pytest) dentro de Docker. Requiere `make docker-build-dev` antes |
| `make lint`            | Corre `ruff check` dentro de Docker. Requiere `make docker-build-dev` antes |
| `make format`          | Formatea el código con `ruff format` dentro de Docker. Requiere `make docker-build-dev` antes |
| `make format-check`    | Verifica el formato sin modificar archivos, dentro de Docker |
| `make docker-build`   | Construye la imagen Docker de producción                    |
| `make docker-build-dev`| Construye la imagen Docker de desarrollo (incluye pytest y ruff) |
| `make docker-run`     | Levanta la app dentro de un contenedor Docker (imagen de producción, sin hot-reload) |
| `make docker-stop`    | Detiene los contenedores en ejecución (producción y dev)     |
| `make docker-shell`   | Abre una shell dentro de la imagen Docker de producción      |
| `make install-hooks`  | Habilita los git hooks del repo (lint en pre-commit)         |

---

## ✅ Tests y Lint

- **Tests**: `pytest` (ver `tests/`). Correr con `make test` (dentro de Docker,
  imagen `avocadodash:dev`) — requiere haber corrido `make docker-build-dev`
  al menos una vez, o al cambiar dependencias.
- **Lint y formato**: [Ruff](https://docs.astral.sh/ruff/) se encarga tanto del
  linting (`make lint`) como del formateo (`make format` / `make format-check`),
  también dentro de Docker.
- **Git hook de pre-commit**: corre `make lint` y `make format-check` antes
  de cada commit (o sea, también dentro de Docker), para que el código nunca
  llegue a `main` sin pasar el lint. Requiere haber corrido
  `make docker-build-dev` al menos una vez. Se activa una sola vez por clon
  del repo con:

  ```bash
  make install-hooks
  ```

  El hook vive versionado en `.githooks/pre-commit` (no en `.git/hooks/`, que
  no se sube al repositorio), y `make install-hooks` simplemente apunta
  `core.hooksPath` a esa carpeta.

---

## 🐳 Docker

Todo el flujo de contenedores pasa por el `Makefile` (`make docker-build`,
`make docker-build-dev`, `make run`, `make test`/`make lint`/`make format*`,
`make docker-run`, `make docker-shell`), que usa `docker build` / `docker
run` directamente sobre el `Dockerfile` — no hay Docker Compose ni Dev
Containers de por medio.

El `Dockerfile` es multi-stage: un stage `base` compartido, un stage `dev`
(con `ruff`/`pytest`, usado por `make test`/`make lint`/`make format*` y
buildeado con `make docker-build-dev`) y el stage `production` (sin
tooling de dev, target por defecto de `docker build`, el que usa Railway).

El flujo recomendado para desarrollar es `make run`: el código se edita en
el host con cualquier editor, pero la app corre dentro del contenedor,
montado como volumen y con `DEBUG=true`, así el reloader de Dash levanta
los cambios al instante sin reiniciar el contenedor. `make test`/`make
lint`/`make format*` montan el mismo volumen sobre la imagen `dev`, así que
siempre corren contra el código actual — pero ninguno de los dos reconstruye
la imagen automáticamente: si cambiás `pyproject.toml`, corré de nuevo
`make docker-build` / `make docker-build-dev`.

---

## 📊 Descripción de los Datos

- **Periodo**: 2015 – 2018  
- **Regiones**: Más de 54 mercados en EE.UU.  
- **Tipos**: Convencional y Orgánico  
- **Métricas**: Precio Promedio, Volumen Total, Códigos PLU (4046, 4225, 4770), Ventas en bolsas (S, L, XL)  

---

## 🎯 Guía de Uso

### Tablero Principal
- Filtra por **Región**, **Tipo** y **Rango de Fechas**  
- Los gráficos se actualizan al instante  

### Gráfica de Dispersión
- Selecciona variables para los ejes **X/Y**  
- Los puntos se colorean por tipo de aguacate  
- Al pasar el cursor se muestra información detallada (región y fecha)  

### Boxplot
- Agrupa por tipo, región o año  
- Identifica valores atípicos y compara distribuciones  

---

## 🌐 Demo en Línea

👉 [AvocadoDash en Railway](https://avocadodash-production.up.railway.app/)

---

## 🤝 Contribuciones

¡Se aceptan Pull Requests!  
Para cambios mayores, abre un issue primero para discutir la propuesta.

---

## 📝 Licencia

Este proyecto está bajo la licencia [MIT](LICENSE).

---

## 🙏 Agradecimientos

- Inspiración del tutorial: [Real Python – Dash Tutorial](https://realpython.com/python-dash/)  
- Fuente de datos: **Hass Avocado Board**

---

## 👨‍💻 Autor

Creado por [@Kuautli](https://github.com/cuauhtemocbe)

---