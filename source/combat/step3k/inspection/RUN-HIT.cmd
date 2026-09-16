@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >toolchain.log 2>&1
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /permissive- /DWIN32_LEAN_AND_MEAN /DNOMINMAX /I"..\..\..\..\native\NVOCombatCore\include" hit-replay.cpp /Fe:hit-replay.exe /link kernel32.lib >hit-build.log 2>&1
if errorlevel 1 exit /b 1
hit-replay.exe >hit-results.txt 2>&1
exit /b %ERRORLEVEL%
