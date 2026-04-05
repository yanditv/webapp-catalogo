@echo off
setlocal

cd /d %~dp0

if not exist .venv (
  call build_windows.bat
  if errorlevel 1 exit /b 1
)

call .venv\Scripts\activate.bat
if errorlevel 1 goto :fail

echo [INFO] Generando ejecutable debug...
pyinstaller --noconfirm webapp-debug.spec
if errorlevel 1 goto :fail

echo.
echo Build debug listo en dist\catalogo-webapp-debug.exe
echo.
exit /b 0

:fail
echo.
echo [ERROR] El build debug no termino correctamente.
echo.
exit /b 1
