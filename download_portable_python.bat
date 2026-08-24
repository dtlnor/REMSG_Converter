@echo off
REM Make a portable python environment in ./python

REM Version info
set PYTHON_VERSION=3.14.7
set PYTHON_VER_SHORT=314

REM Delete ./python if exist
if exist python rmdir /s python

REM Download embeddable python
curl -OL https://www.python.org/ftp/python/%PYTHON_VERSION%/python-%PYTHON_VERSION%-embed-amd64.zip
powershell Expand-Archive -Force -Path python-%PYTHON_VERSION%-embed-amd64.zip
del python-%PYTHON_VERSION%-embed-amd64.zip
cd python-%PYTHON_VERSION%-embed-amd64

REM Download mmh3 and chardet
(
    echo python%PYTHON_VER_SHORT%.zip
    echo .
    echo import site
) > python%PYTHON_VER_SHORT%._pth
curl -OL https://bootstrap.pypa.io/get-pip.py
python get-pip.py
REM If you have the requirements installed in any path, uninstall them.
python -m pip install -r ..\requirements.txt
robocopy Lib\site-packages\chardet chardet /E
copy Lib\site-packages\mmh3.cp%PYTHON_VER_SHORT%-win_amd64.pyd .
rmdir /s /q Lib Scripts
del get-pip.py

REM Remove path config file
del python%PYTHON_VER_SHORT%._pth
cd ..

REM Rename folder
rename python-%PYTHON_VERSION%-embed-amd64 python

pause
