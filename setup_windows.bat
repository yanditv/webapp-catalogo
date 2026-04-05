@echo off
setlocal

cd /d %~dp0

set "PYTHON_CMD="

call :pick_python "py -3.11"
if not defined PYTHON_CMD call :pick_python "py -3"
if not defined PYTHON_CMD call :pick_python "python"

if not defined PYTHON_CMD (
  echo [ERROR] No se encontro Python compatible.
  echo Instala Python 3.11 o 3.12 en la maquina de preparacion.
  exit /b 1
)

if not exist .venv (
  echo [INFO] Creando entorno virtual...
  call %PYTHON_CMD% -m venv .venv
  if errorlevel 1 goto :fail
)

call .venv\Scripts\activate.bat
if errorlevel 1 goto :fail

echo [INFO] Actualizando pip...
python -m pip install --upgrade pip
if errorlevel 1 goto :fail

echo [INFO] Instalando dependencias...
pip install -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo [OK] Entorno listo.
echo Usa run_windows.bat para iniciar la app.
echo.
exit /b 0

:pick_python
call %~1 -c "import sys; print(sys.version)" >nul 2>nul
if not errorlevel 1 set "PYTHON_CMD=%~1"
exit /b 0

:fail
echo.
echo [ERROR] La preparacion no termino correctamente.
echo.
exit /b 1
