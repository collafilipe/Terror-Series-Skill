@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist elevenlabs_key.txt type nul > elevenlabs_key.txt
echo.
echo  Vai abrir o Bloco de Notas. Cole a sua chave de API do ElevenLabs, salve (Ctrl+S) e feche.
echo.
notepad elevenlabs_key.txt
echo  Conferindo a chave e listando as vozes da sua conta...
echo.
"..\.venv\Scripts\python.exe" eleven.py listar
echo.
pause
