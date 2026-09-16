@echo off
setlocal
cd /d "%~dp0"
if not exist out-coverage mkdir out-coverage
call "C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >out-coverage\toolchain.log 2>&1
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- CoverageProfiles.cpp coverage_tests.cpp /Fo:out-coverage\ /Fe:out-coverage\coverage_checks.exe /link /INCREMENTAL:NO >out-coverage\build.log 2>&1
if errorlevel 1 exit /b 1
out-coverage\coverage_checks.exe >out-coverage\results.txt 2>&1
exit /b %ERRORLEVEL%
