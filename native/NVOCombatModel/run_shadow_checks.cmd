@echo off
setlocal
cd /d "%~dp0"
if not exist out mkdir out
call "C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >out\shadow-toolchain.log 2>&1
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- ArmourModel.cpp ShadowAdapter.cpp shadow_adapter_tests.cpp /Fo:out\ /Fe:out\shadow_adapter_checks.exe /link /INCREMENTAL:NO >out\shadow-build.log 2>&1
if errorlevel 1 exit /b 1
out\shadow_adapter_checks.exe >out\shadow-results.txt 2>&1
exit /b %ERRORLEVEL%
