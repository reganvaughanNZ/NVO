@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0"
if errorlevel 1 exit /b 1
if not exist out mkdir out
set "NVO_CAPTURE_VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%NVO_CAPTURE_VSWHERE%" goto missing
set "NVO_CAPTURE_VS="
for /f "usebackq delims=" %%I in (`call "%NVO_CAPTURE_VSWHERE%" -latest -products * -version "[17.0,19.0)" -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "NVO_CAPTURE_VS=%%I"
if not defined NVO_CAPTURE_VS goto missing
call "%NVO_CAPTURE_VS%\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >out\copy-capture-toolchain.log 2>&1
if errorlevel 1 goto failed
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- /I"..\include" CopyCaptureTests.cpp "..\src\ArmourSnapshot.cpp" /Foout\ /Feout\CopyCaptureTests.exe /link /INCREMENTAL:NO >out\copy-capture-build.log 2>&1
if errorlevel 1 goto failed
out\CopyCaptureTests.exe >out\copy-capture-results.txt 2>&1
if errorlevel 1 goto failed
type out\copy-capture-results.txt
popd
exit /b 0
:missing
echo MSVC x86 tools missing. No software was installed.
:failed
echo Check failed. Inspect out\copy-capture logs and results. No game files were accessed.
popd
exit /b 1
