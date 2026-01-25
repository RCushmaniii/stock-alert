@echo off
cd /d "%~dp0"
set PATH=C:\LangAppFiles\anaconda3\Library\bin;C:\LangAppFiles\anaconda3;%SYSTEMROOT%\system32;%SYSTEMROOT%
start "" /B "%~dp0venv\Scripts\pythonw.exe" -m stockalert
exit
