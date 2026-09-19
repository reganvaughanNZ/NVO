@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0"
if errorlevel 1 exit /b 1
if not exist out mkdir out
set "NVO_LIFECYCLE_VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%NVO_LIFECYCLE_VSWHERE%" goto missing
set "NVO_LIFECYCLE_VS="
for /f "usebackq delims=" %%I in (`call "%NVO_LIFECYCLE_VSWHERE%" -latest -products * -version "[17.0,19.0)" -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "NVO_LIFECYCLE_VS=%%I"
if not defined NVO_LIFECYCLE_VS goto missing
call "%NVO_LIFECYCLE_VS%\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >out\projectile-lifecycle-toolchain.log 2>&1
if errorlevel 1 goto failed
cl /nologo /MT /O2 /Gy /std:c++17 /EHsc /W4 /WX /permissive- /I"..\include" ProjectileLifecycleTests.cpp /Foout\ /Feout\ProjectileLifecycleTests.exe /link /OPT:REF /INCREMENTAL:NO >out\projectile-lifecycle-build.log 2>&1
if errorlevel 1 goto failed
out\ProjectileLifecycleTests.exe >out\projectile-lifecycle-results.txt 2>&1
set "NVO_LIFECYCLE_RESULT=%ERRORLEVEL%"
type out\projectile-lifecycle-results.txt
popd
exit /b %NVO_LIFECYCLE_RESULT%
:missing
echo MSVC x86 tools missing. No software was installed.
:failed
if exist out\projectile-lifecycle-build.log type out\projectile-lifecycle-build.log
echo Check failed. Inspect out\projectile-lifecycle logs and results. No game files were accessed.
popd
exit /b 1
