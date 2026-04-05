@echo off
setlocal

cd /d %~dp0

if not exist .venv (
  py -3.11 -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-build.txt

pyinstaller --noconfirm webapp.spec

echo.
echo Build listo en dist\catalogo-webapp.exe
echo.
