@echo off
setlocal EnableExtensions DisableDelayedExpansion
call "C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >nul
if errorlevel 1 exit /b 1
pushd "%~dp0"
if not exist out mkdir out
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- /I"..\include" SpawnCallTests.cpp /Foout\SpawnCallTests.obj /Feout\SpawnCallTests.exe >out\build.log 2>&1
if errorlevel 1 (type out\build.log & popd & exit /b 1)
out\SpawnCallTests.exe >out\checks.txt
set "NVO_CHECK_RESULT=%ERRORLEVEL%"
type out\checks.txt
popd
exit /b %NVO_CHECK_RESULT%
