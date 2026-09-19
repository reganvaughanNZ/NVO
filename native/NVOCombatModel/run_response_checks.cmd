@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0"
if errorlevel 1 exit /b 1
if not exist out-response mkdir out-response
set "NVO_RESPONSE_VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%NVO_RESPONSE_VSWHERE%" goto missing
set "NVO_RESPONSE_VS="
for /f "usebackq delims=" %%I in (`call "%NVO_RESPONSE_VSWHERE%" -latest -products * -version "[17.0,19.0)" -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "NVO_RESPONSE_VS=%%I"
if not defined NVO_RESPONSE_VS goto missing
call "%NVO_RESPONSE_VS%\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >out-response\toolchain.log 2>&1
if errorlevel 1 goto failed
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- ResponseDefinitions.cpp response_definition_tests.cpp /Fo:out-response\ /Fe:out-response\response_checks.exe /link /INCREMENTAL:NO >out-response\build.log 2>&1
if errorlevel 1 goto failed
out-response\response_checks.exe >out-response\results.txt 2>&1
set "NVO_RESPONSE_RESULT=%ERRORLEVEL%"
type out-response\results.txt
popd
exit /b %NVO_RESPONSE_RESULT%
:missing
echo MSVC x86 tools missing. This runner does not install anything.
:failed
popd
exit /b 1
