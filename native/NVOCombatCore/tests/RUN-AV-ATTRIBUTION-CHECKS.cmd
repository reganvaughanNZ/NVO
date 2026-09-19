@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0"
if errorlevel 1 exit /b 1
set "NVO_VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
set "NVO_VSINSTALL="
if not exist out mkdir out
for /f "usebackq delims=" %%I in (`call "%NVO_VSWHERE%" -latest -products * -version "[17.0,19.0)" -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "NVO_VSINSTALL=%%I"
if not defined NVO_VSINSTALL (popd & exit /b 1)
call "%NVO_VSINSTALL%\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >out\av-attribution-toolchain.log 2>&1
if errorlevel 1 (popd & exit /b 1)
cl /nologo /MT /O2 /Gy /std:c++17 /EHsc /W4 /WX /permissive- /I"..\include" ActorValueAttributionTests.cpp /Foout\ /Feout\ActorValueAttributionTests.exe /link /OPT:REF >out\av-attribution-build.log 2>&1
if errorlevel 1 (type out\av-attribution-build.log & popd & exit /b 1)
out\ActorValueAttributionTests.exe >out\av-attribution-results.txt
set "NVO_CHECK_RESULT=%ERRORLEVEL%"
type out\av-attribution-results.txt
popd
exit /b %NVO_CHECK_RESULT%
