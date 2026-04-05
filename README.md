# Catálogos — Editor web

App web local para crear y personalizar catálogos en PDF. Editor visual para un
solo usuario con SQLite + FastAPI + WeasyPrint.

## Features
- Crea **N catálogos**, duplícalos, elimínalos.
- Edita empresa, tagline, descripción, contacto, redes sociales, recomendaciones.
- CRUD de productos con subida y optimización de imágenes.
- Reordena productos (↑ ↓).
- Elige entre **varias plantillas PDF** (Editorial Premium, Minimal Clean).
- Personaliza colores del tema por catálogo.
- **Vista previa** del PDF embebida y **descarga** directa.

## Requisitos
- Python 3.9+
- En macOS: Homebrew con `pango`, `cairo`, `glib` para WeasyPrint.
  ```bash
  brew install pango cairo glib
  ```

## Setup
```bash
cd webapp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Sembrar el catálogo inicial con los 6 productos de SALUD Y BIENESTAR/
.venv/bin/python seed.py
```

## Ejecutar
```bash
.venv/bin/uvicorn main:app --reload
```
Abrir http://127.0.0.1:8000

## Docker

### Construir la imagen
```bash
cd webapp
docker build -t catalogo-webapp .
```

### Ejecutar con Docker
```bash
docker run --rm -p 8000:8000 \
  -v "$(pwd)/data:/app/data" \
  --name catalogo-webapp \
  catalogo-webapp
```

Abrir http://127.0.0.1:8000

### Ejecutar con Docker Compose
```bash
cd webapp
docker compose up --build
```

### Sembrar catálogo inicial dentro del contenedor
Si necesitas cargar los 6 productos base dentro del volumen `data/`:

```bash
docker compose run --rm webapp python seed.py
```

Notas:
- `data/` se monta como volumen para conservar la base SQLite y las imágenes subidas.
- El contenedor expone la app en el puerto `8000`.
- El `Dockerfile` ya incluye las librerías del sistema que necesita WeasyPrint.

## Ejecutable para Windows

La app quedó preparada para empaquetarse como `.exe` usando PyInstaller.

### Archivos agregados para build
- `launcher.py`: inicia Uvicorn y abre el navegador automáticamente.
- `webapp.spec`: incluye `static/`, `ui_templates/`, `pdf_templates/` y `fonts/` dentro del ejecutable.
- `requirements-build.txt`: dependencias de build.
- `build_windows.bat`: script de compilación para Windows.

### Compilar en Windows
```bat
cd webapp
build_windows.bat
```

El ejecutable se genera en:

```bat
dist\catalogo-webapp.exe
```

### Compilar una version debug con consola visible
Si el ejecutable normal no abre o no da pistas, genera esta variante:

```bat
cd webapp
build_windows_debug.bat
```

Salida esperada:

```bat
dist\catalogo-webapp-debug.exe
```

Esta version abre una consola y muestra errores de arranque directamente.

### Ejecutar el `.exe`
- Al abrirlo, la app levanta un servidor local en `http://127.0.0.1:8000`.
- También intenta abrir el navegador automáticamente.
- La base SQLite y los uploads se guardan en `data\` junto al ejecutable.

### Variables opcionales
Puedes cambiar host o puerto con variables de entorno:

```bat
set CATALOGOS_HOST=127.0.0.1
set CATALOGOS_PORT=8000
catalogo-webapp.exe
```

### Nota importante sobre WeasyPrint en Windows
Para que la generación de PDF funcione en Windows, la máquina de build y de uso debe tener disponibles las librerías nativas que WeasyPrint necesita. Si al exportar PDF ves errores relacionados con GTK, Pango o Cairo, instala el runtime correspondiente en Windows antes de compilar o ejecutar el `.exe`.

## Estructura
```
webapp/
├── main.py              # FastAPI app + rutas
├── db.py                # SQLAlchemy engine + SQLite
├── models.py            # Catalog, Product
├── pdf_service.py       # Renderizador HTML → PDF (WeasyPrint)
├── seed.py              # Migración inicial
├── pdf_templates/       # Plantillas PDF
│   ├── editorial/       # Editorial Premium (A4 landscape, tipo revista)
│   └── minimal/         # Minimal Clean (A4 portrait, limpio)
├── ui_templates/        # Plantillas Jinja2 del admin
├── static/              # CSS/JS del admin
├── fonts/               # TTF (Lora, Raleway)
└── data/                # SQLite + uploads (gitignored)
    ├── catalogs.db
    └── uploads/
```

## Agregar una nueva plantilla PDF
1. Crear `pdf_templates/mi_plantilla/template.html` — accede a `{{ company }}`,
   `{{ products }}`, `{{ socials }}`, `{{ tips }}`, `{{ theme }}`.
2. Agregar `pdf_templates/mi_plantilla/meta.txt` con título y descripción.
3. Reiniciar el servidor — la nueva plantilla aparecerá en el editor.
