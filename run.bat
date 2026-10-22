@echo off
setlocal
echo Mini JARVIS quick start
echo Create and activate a virtual environment, then install requirements first.
echo Starting the private FastAPI backend on http://127.0.0.1:8000
start "Mini JARVIS Backend" cmd /k "uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000"
timeout /t 2 /nobreak >nul
echo Starting the private Streamlit frontend on http://127.0.0.1:8501
start "Mini JARVIS Frontend" cmd /k "streamlit run frontend/app.py --server.address 127.0.0.1 --server.port 8501"
endlocal
