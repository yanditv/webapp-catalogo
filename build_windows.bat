@echo off
setlocal

cd /d %~dp0

set "PYTHON_CMD="

if not exist .venv (
  call :try_create_venv "py -3.11" "Python 3.11"
  if not defined PYTHON_CMD call :try_create_venv "py -3" "Python 3"
  if not defined PYTHON_CMD call :try_create_venv "python" "python en PATH"

  if not defined PYTHON_CMD (
    echo [ERROR] No se pudo crear el entorno virtual.
    echo Instala Python 3.11 o 3.12 en la maquina de build y vuelve a intentar.
    exit /b 1
  )
) else (
  echo [INFO] Usando entorno virtual existente.
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

:try_create_venv
set "TRY_CMD=%~1"
set "TRY_LABEL=%~2"
echo [INFO] Intentando crear entorno virtual con %TRY_LABEL%...
call %TRY_CMD% -m venv .venv >nul 2>nul
if errorlevel 1 (
  if exist .venv rmdir /s /q .venv >nul 2>nul
  exit /b 0
)
set "PYTHON_CMD=%TRY_CMD%"
echo [INFO] Entorno virtual creado con %TRY_LABEL%.
exit /b 0

:fail
echo.
echo [ERROR] El build no termino correctamente.
echo Si no se creo la carpeta dist\, revisa el primer error mostrado arriba.
echo.
exit /b 1
