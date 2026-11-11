@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
 py -3.11 -m venv .venv
 if errorlevel 1 goto fail
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
echo Abra http://127.0.0.1:8502 no Edge ou Chrome.
.venv\Scripts\python.exe -m uvicorn live:app --host 127.0.0.1 --port 8502 --ws-max-size 6000000
pause
exit /b
:fail
echo Confira Python 3.11 e internet para instalar dependencias.
pause
