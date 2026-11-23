@echo off
title Iniciar Streamlit - Mineria de Datos Hurtos Colombia
cd /d "%~dp0"
echo ========================================================
echo Iniciando aplicacion interactiva de Streamlit (EDA)...
echo URL: http://localhost:8501
echo ========================================================
streamlit run app.py
pause
