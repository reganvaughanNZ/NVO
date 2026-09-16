@echo off
setlocal
cd /d "%~dp0"
if not exist out-admission mkdir out-admission
call "C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >out-admission\toolchain.log 2>&1
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- ArmourModel.cpp AdmissionLedger.cpp admission_tests.cpp /Fo:out-admission\ /Fe:out-admission\admission_checks.exe /link /INCREMENTAL:NO >out-admission\build.log 2>&1
if errorlevel 1 exit /b 1
out-admission\admission_checks.exe >out-admission\results.txt 2>&1
exit /b %ERRORLEVEL%
