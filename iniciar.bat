@echo off
setlocal

set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"
set "BACKEND=%ROOT%backend"
set "FRONTEND=%ROOT%frontend"

if not exist "%PYTHON%" (
    echo [ERRO] Ambiente Python nao encontrado em .venv.
    echo Crie o ambiente com: py -3.11 -m venv .venv
    pause
    exit /b 1
)

if not exist "%BACKEND%\requirements.txt" (
    echo [ERRO] Arquivo backend\requirements.txt nao encontrado.
    pause
    exit /b 1
)

"%PYTHON%" -c "import fastapi, openai, google.genai" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando dependencias do backend...
    "%PYTHON%" -m pip install -r "%BACKEND%\requirements.txt"
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar as dependencias do backend.
        pause
        exit /b 1
    )
)

if not exist "%BACKEND%\.env" (
    echo [ERRO] Arquivo backend\.env nao encontrado.
    echo Copie backend\.env.example para backend\.env e configure os valores.
    pause
    exit /b 1
)

if not exist "%FRONTEND%\package.json" (
    echo [ERRO] Frontend nao encontrado em frontend\.
    pause
    exit /b 1
)

if not exist "%FRONTEND%\node_modules" (
    echo [INFO] Instalando dependencias do frontend...
    call npm install --prefix "%FRONTEND%"
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar as dependencias do frontend.
        pause
        exit /b 1
    )
)

netstat -ano | findstr /R /C:":8000 .*LISTENING" >nul
if errorlevel 1 (
    start "CDM API" /D "%BACKEND%" cmd.exe /k ""%PYTHON%" -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"
) else (
    echo [INFO] A API ja esta rodando na porta 8000.
)

netstat -ano | findstr /R /C:":5173 .*LISTENING" >nul
if errorlevel 1 (
    start "CDM Frontend" /D "%FRONTEND%" cmd.exe /k npm run dev -- --host 127.0.0.1
) else (
    echo [INFO] O frontend ja esta rodando na porta 5173.
)

ping 127.0.0.1 -n 4 >nul
start "" http://localhost:5173

echo.
echo [OK] Projeto iniciado.
echo Frontend: http://localhost:5173
echo API:      http://localhost:8000
endlocal
