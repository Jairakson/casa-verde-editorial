@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
echo CASA E VERDE - Conector ChatGPT Plus
where py >nul 2>nul
if %errorlevel%==0 (
  set "CASAVERDE_PY=py -3"
) else (
  set "CASAVERDE_PY=python"
)
%CASAVERDE_PY% -c "import sys; assert sys.version_info >= (3,11)" >nul 2>nul
if errorlevel 1 (
  echo Instale Python 3.11 ou superior em https://www.python.org/downloads/windows/
  echo Marque Add Python to PATH na instalacao. Depois abra este arquivo novamente.
  pause
  exit /b 1
)
if not exist ".venv-connector\Scripts\python.exe" (
  %CASAVERDE_PY% -m venv .venv-connector
  if errorlevel 1 goto erro
)
".venv-connector\Scripts\python.exe" -m pip install --disable-pip-version-check -r connector\requirements.txt
if errorlevel 1 goto erro
".venv-connector\Scripts\python.exe" -m connector.desktop
pause
exit /b 0
:erro
echo Nao foi possivel preparar o conector. Confira sua conexao e a instalacao do Python.
pause
exit /b 1
