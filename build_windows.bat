@echo off
setlocal

cd /d %~dp0

set "PYTHON_CMD="
set "PYTHON_LABEL="
where py >nul 2>nul
if %errorlevel%==0 (
  py -3.11 -c "import sys; print(sys.version)" >nul 2>nul
  if %errorlevel%==0 (
    set "PYTHON_CMD=py -3.11"
    set "PYTHON_LABEL=Python 3.11"
  )
)
if not defined PYTHON_CMD (
  where py >nul 2>nul
  if %errorlevel%==0 (
    py -3 -c "import sys; print(sys.version)" >nul 2>nul
    if %errorlevel%==0 (
      set "PYTHON_CMD=py -3"
      set "PYTHON_LABEL=Python 3"
    )
  )
)
if not defined PYTHON_CMD (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set "PYTHON_CMD=python"
    set "PYTHON_LABEL=python en PATH"
  )
)

if not defined PYTHON_CMD (
  echo [ERROR] No se encontro Python en PATH.
  echo Instala Python 3.11+ y vuelve a ejecutar este script.
  exit /b 1
)

if not exist .venv (
  echo [INFO] Creando entorno virtual con %PYTHON_LABEL%...
  %PYTHON_CMD% -m venv .venv
  if errorlevel 1 goto :fail
)

call .venv\Scripts\activate.bat
if errorlevel 1 goto :fail

echo [INFO] Actualizando pip...
python -m pip install --upgrade pip
if errorlevel 1 goto :fail

echo [INFO] Instalando dependencias...
pip install -r requirements.txt -r requirements-build.txt
if errorlevel 1 goto :fail

echo [INFO] Generando ejecutable...
pyinstaller --noconfirm webapp.spec
if errorlevel 1 goto :fail

echo.
echo Build listo en dist\catalogo-webapp.exe
echo.
exit /b 0

:fail
echo.
echo [ERROR] El build no termino correctamente.
echo Si no se creo la carpeta dist\, revisa el primer error mostrado arriba.
echo.
exit /b 1
