@echo off
REM Loop through all .msg.17 files in the msg/ directory
FOR %%F IN (msg\*.msg.17) DO (
    REM Provide 'en' input automatically and pass each file to msg2txt.bat
    echo en | CALL msg2txt.bat "%%F"
)