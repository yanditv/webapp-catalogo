@echo off
setlocal

cd /d %~dp0

set "SRC=C:\msys64\ucrt64\bin"
set "DST=%~dp0gtk-runtime\bin"

if not exist "%SRC%" (
  echo [ERROR] No existe %SRC%
  echo Instala MSYS2/GTK o ajusta este script a la ruta correcta.
  exit /b 1
)

if not exist "%DST%" (
  mkdir "%DST%"
)

echo [INFO] Copiando runtime GTK...
xcopy "%SRC%\*" "%DST%\" /E /I /Y >nul
if errorlevel 1 goto :fail

echo [OK] GTK copiado en:
echo %DST%
exit /b 0

:fail
echo [ERROR] No se pudo copiar el runtime GTK.
exit /b 1
