@echo off
cd /d %~dp0

echo Available languages:
echo Japanese: ja
echo English: en
echo French: fr
echo Italian: it
echo German: de
echo Spanish: es
echo Russian: ru
echo Polish: pl
echo Dutch: nl
echo Portuguese: pt
echo PortugueseBr: ptbr
echo Korean: ko
echo TraditionalChinese: zhtw
echo SimplifiedChinese: zhcn
echo Finnish: fi
echo Swedish: sv
echo Danish: da
echo Norwegian: no
echo Czech: cs
echo Hungarian: hu
echo Slovak: sk
echo Arabic: ar
echo Turkish: tr
echo Bulgarian: bg
echo Greek: el
echo Romanian: ro
echo Thai: th
echo Ukrainian: ua
echo Vietnamese: vi
echo Indonesian: id
echo Fiction: cc
echo Hindi: hi
echo LatinAmericanSpanish: es419

set /p lang="Please enter one of the language codes above: "

REM Loop through all .msg.17 files in the folder
for %%F in (*.msg.17) do (
    REMSG_Converter.exe -i "%%F" -m json -l %lang%
)

pause