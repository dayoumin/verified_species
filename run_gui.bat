echo off
cd /d %~dp0
call .venv\Scripts\activate.bat
python -m species_verifier.gui.app
pause