@echo off

set /P c=Do you have a 64-bit version of Python installed? [Y/N] 
if /I "%c%" EQU "Y" goto :py64
else goto :py32

:py32
pip install curses-2.2-cp27-none-win32.whl
goto :end

:py64
pip install curses-2.2-cp27-none-win_amd64.whl
goto :end

:end
PAUSE