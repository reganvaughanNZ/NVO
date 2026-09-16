@echo off
setlocal
cd /d "%~dp0"
if not exist out mkdir out
call "C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >out\toolchain.log 2>&1
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- ArmourModel.cpp tests.cpp /Fo:out\ /Fe:out\model_checks.exe /link /INCREMENTAL:NO >out\build.log 2>&1
if errorlevel 1 exit /b 1
out\model_checks.exe >out\results.txt 2>&1
exit /b %ERRORLEVEL%
