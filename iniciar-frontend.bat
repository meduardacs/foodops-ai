@echo off
setlocal
cd /d "%~dp0frontend"
echo ==========================================
echo FoodOps AI - Frontend / React
 echo ==========================================
where npm >nul 2>nul
if errorlevel 1 goto :fail
if not exist "node_modules\react" (
  echo Instalando dependencias npm...
  call npm install
  if errorlevel 1 goto :fail
)
echo.
echo Acesse http://localhost:5173
call npm run dev
goto :end
:fail
echo.
echo Nao foi possivel iniciar o frontend. Verifique Node.js e sua conexao.
pause
:end
endlocal
