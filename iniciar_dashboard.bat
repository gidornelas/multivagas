@echo off
title Multivagas — Dashboard

REM Inicia o servidor API em uma janela separada
start "Multivagas API" cmd /k "py api_server.py"

REM Aguarda 1 segundo para o servidor subir
timeout /t 1 /nobreak >nul

REM Abre o dashboard no browser padrão
start "" "%~dp0dashboard.html"

echo.
echo Servidor API iniciado e dashboard aberto.
echo Feche a janela "Multivagas API" para encerrar.
