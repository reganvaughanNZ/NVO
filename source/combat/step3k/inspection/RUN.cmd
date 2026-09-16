@echo off
setlocal
call "C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >toolchain.log 2>&1
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /permissive- /DWIN32_LEAN_AND_MEAN /DNOMINMAX /I"..\..\..\..\native\NVOCombatCore\include" replay.cpp /Fe:replay.exe /link /BASE:0x20000000 /DYNAMICBASE:NO kernel32.lib >build.log 2>&1
if errorlevel 1 exit /b 1
replay.exe >results.txt 2>&1
exit /b %ERRORLEVEL%
