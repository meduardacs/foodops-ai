@echo off
setlocal
cd /d "%~dp0backend"
echo ==========================================
echo FoodOps AI - Backend / FastAPI
echo ==========================================
if not exist ".venv\Scripts\python.exe" (
  echo Criando ambiente virtual Python...
  py -m venv .venv
  if errorlevel 1 (
    echo Falha com py. Tentando python...
    python -m venv .venv
    if errorlevel 1 goto :fail
  )
)
call ".venv\Scripts\activate.bat"
python -m pip install -r requirements.txt
if errorlevel 1 goto :fail
echo.
echo API: http://localhost:8000
python -m uvicorn app.main:app --reload --port 8000
goto :end
:fail
echo.
echo Falha na inicializacao. Confirme Python instalado e internet para a primeira instalacao.
pause
:end
endlocal
