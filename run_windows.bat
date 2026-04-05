@echo off
setlocal

cd /d %~dp0

set "HOST=127.0.0.1"
set "PORT=8000"

if not exist .venv\Scripts\python.exe (
  echo [ERROR] No existe .venv\Scripts\python.exe
  echo Primero crea el entorno virtual e instala dependencias.
  echo.
  echo Ejemplo:
  echo   py -3.11 -m venv .venv
  echo   .venv\Scripts\python -m pip install -r requirements.txt
  exit /b 1
)

if exist "%~dp0gtk-runtime\bin" (
  set "PATH=%~dp0gtk-runtime\bin;%PATH%"
)

set "CATALOGOS_HOST=%HOST%"
set "CATALOGOS_PORT=%PORT%"

start "" http://%HOST%:%PORT%

echo [INFO] Iniciando Catalogos en http://%HOST%:%PORT%
echo [INFO] Cierra esta ventana para detener el servidor.

.venv\Scripts\python launcher.py
