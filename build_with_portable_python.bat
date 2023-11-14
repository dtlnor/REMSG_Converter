@echo off
REM Make a release package (REMSG_Converter.zip)
if exist release rmdir /s release
mkdir release\src

REM Edit batch files and put them in ./release
set OLD_STR=REMSG_Converter.exe
set NEW_STR=python\python.exe src\main.py

setlocal enabledelayedexpansion
for %%f in (bat\*.bat) DO (
  for /f "delims=" %%a in (%%f) do (
    set line=%%a
    echo !line:%OLD_STR%=%NEW_STR%!>>release\%%~nxf
  )
)

REM Put other files in ./release
copy src\*.py release\src
copy requirements.txt release
cd release
echo|..\download_portable_python.bat
del requirements.txt

REM Zip ./release
powershell Compress-Archive -Force -Path * -Destination ../REMSG_Converter.zip

echo Done!
pause
