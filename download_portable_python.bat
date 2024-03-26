@echo off
REM Make a portable python environment in ./python

REM Version info
set PYTHON_VERSION=3.12.2
set PYTHON_VER_SHORT=312

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
cd chardet
rmdir /s /q __pycache__ cli metadata\__pycache__
cd ..

REM Remove unnecessary files
del pythonw.exe python.cat python%PYTHON_VER_SHORT%._pth
del python3.dll libcrypto-1_1.dll libssl-1_1.dll libcrypto-3.dll libssl-3.dll sqlite3.dll
del vcruntime140.dll vcruntime140_1.dll
del _asyncio.pyd _bz2.pyd _decimal.pyd _elementtree.pyd _hashlib.pyd
del _lzma.pyd _msi.pyd _overlapped.pyd _queue.pyd
del _sqlite3.pyd _ssl.pyd _zoneinfo.pyd
del pyexpat.pyd unicodedata.pyd winsound.pyd

REM Remove unnecessary files from pythonXXX.zip
powershell Expand-Archive -Force -Path python%PYTHON_VER_SHORT%.zip
cd python%PYTHON_VER_SHORT%
rmdir /s /q __phello__ curses dbm html http lib2to3 msilib
rmdir /s /q pydoc_data site-packages sqlite3 tomllib urllib
rmdir /s /q wsgiref xml xmlrpc zoneinfo
del ast.pyc calendar.pyc doctest.pyc ftplib.pyc
del imaplib.pyc ipaddress.pyc mailbox.pyc nntplib.pyc
del optparse.pyc pdb.pyc pickletools.pyc pydoc.pyc
del smtpd.pyc smtplib.pyc ssl.pyc tarfile.pyc
powershell Compress-Archive -Force -Path * -Destination ../python%PYTHON_VER_SHORT%.zip
cd ..
rmdir /s /q python%PYTHON_VER_SHORT%
cd ..

REM Rename folder
rename python-%PYTHON_VERSION%-embed-amd64 python

pause
