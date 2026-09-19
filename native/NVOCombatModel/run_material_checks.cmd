@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0"
if errorlevel 1 exit /b 1
if not exist out-material mkdir out-material
set "NVO_MATERIAL_VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
if not exist "%NVO_MATERIAL_VSWHERE%" goto missing
set "NVO_MATERIAL_VS="
for /f "usebackq delims=" %%I in (`call "%NVO_MATERIAL_VSWHERE%" -latest -products * -version "[17.0,19.0)" -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "NVO_MATERIAL_VS=%%I"
if not defined NVO_MATERIAL_VS goto missing
call "%NVO_MATERIAL_VS%\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >out-material\toolchain.log 2>&1
if errorlevel 1 goto failed
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- ArmourModel.cpp ShadowAdapter.cpp ResponseDefinitions.cpp ImpactBinding.cpp MaterialPreview.cpp material_preview_tests.cpp /Fo:out-material\ /Fe:out-material\material_checks.exe /link /INCREMENTAL:NO >out-material\material-build.log 2>&1
if errorlevel 1 goto failed
out-material\material_checks.exe >out-material\material-results.txt 2>&1
if errorlevel 1 goto failed
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- ArmourModel.cpp tests.cpp /Fo:out-material\ /Fe:out-material\model_checks.exe /link /INCREMENTAL:NO >out-material\model-build.log 2>&1
if errorlevel 1 goto failed
out-material\model_checks.exe >out-material\model-results.txt 2>&1
if errorlevel 1 goto failed
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- ArmourModel.cpp ShadowAdapter.cpp shadow_adapter_tests.cpp /Fo:out-material\ /Fe:out-material\shadow_checks.exe /link /INCREMENTAL:NO >out-material\shadow-build.log 2>&1
if errorlevel 1 goto failed
out-material\shadow_checks.exe >out-material\shadow-results.txt 2>&1
if errorlevel 1 goto failed
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- ResponseDefinitions.cpp response_definition_tests.cpp /Fo:out-material\ /Fe:out-material\response_checks.exe /link /INCREMENTAL:NO >out-material\response-build.log 2>&1
if errorlevel 1 goto failed
out-material\response_checks.exe >out-material\response-results.txt 2>&1
if errorlevel 1 goto failed
type out-material\material-results.txt
type out-material\model-results.txt
type out-material\shadow-results.txt
type out-material\response-results.txt
popd
exit /b 0
:missing
echo MSVC x86 tools missing. No software was installed.
:failed
echo Check failed. Inspect out-material logs and results. No game files were accessed.
popd
exit /b 1
