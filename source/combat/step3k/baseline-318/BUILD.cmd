@echo off
setlocal EnableExtensions DisableDelayedExpansion
title NVOCombatCore - native build
pushd "%~dp0"
if errorlevel 1 exit /b 1
set "NVO_PROJECT_DIR=%CD%"
set "NVO_VSWHERE=%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe"
set "NVO_VSINSTALL="
if not exist "%NVO_VSWHERE%" goto missing_tools
for /f "usebackq delims=" %%I in (`call "%NVO_VSWHERE%" -latest -products * -version "[17.0,19.0)" -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath`) do set "NVO_VSINSTALL=%%I"
if not defined NVO_VSINSTALL goto missing_tools
if not exist "%NVO_VSINSTALL%\Common7\Tools\VsDevCmd.bat" goto missing_tools

if not exist "out" mkdir "out"
if not exist "out" goto folder_error
:choose_output
set "NVO_BUILD_DIR=%NVO_PROJECT_DIR%\out\build-%RANDOM%-%RANDOM%"
if exist "%NVO_BUILD_DIR%" goto choose_output
mkdir "%NVO_BUILD_DIR%"
if not exist "%NVO_BUILD_DIR%" goto folder_error

echo Configuring the installed Visual Studio x86 compiler...
call "%NVO_VSINSTALL%\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >"%NVO_BUILD_DIR%\toolchain.log" 2>&1
if errorlevel 1 goto toolchain_error
where cl.exe >nul 2>&1
if errorlevel 1 goto toolchain_error

pushd "%NVO_BUILD_DIR%"
if errorlevel 1 goto folder_error
echo Building NVOCombatCore. This does not install or run the DLL.
cl.exe /nologo /Bv /LD /MT /O2 /Zi /FdNVOCombatCore-compile.pdb /std:c++17 /EHsc /W4 /permissive- /DWIN32_LEAN_AND_MEAN /DNOMINMAX /I"%NVO_PROJECT_DIR%\include" "%NVO_PROJECT_DIR%\src\Plugin.cpp" "%NVO_PROJECT_DIR%\src\NativeLog.cpp" "%NVO_PROJECT_DIR%\src\NativeObserver.cpp" "%NVO_PROJECT_DIR%\src\CurrentHit.cpp" "%NVO_PROJECT_DIR%\src\DamageEvents.cpp" "%NVO_PROJECT_DIR%\src\HitTransaction.cpp" "%NVO_PROJECT_DIR%\src\FlightPreview.cpp" "%NVO_PROJECT_DIR%\src\FlightTiming.cpp" "%NVO_PROJECT_DIR%\src\FlightPhysics.cpp" /link /DEBUG:FULL /OPT:REF /OPT:ICF /PDB:NVOCombatCore.pdb /MACHINE:X86 /DEF:"%NVO_PROJECT_DIR%\src\Exports.def" /OUT:NVOCombatCore.dll /IMPLIB:NVOCombatCore.lib kernel32.lib >build.log 2>&1
set "NVO_BUILD_RESULT=%ERRORLEVEL%"
if not "%NVO_BUILD_RESULT%"=="0" goto compile_error
if not exist "NVOCombatCore.dll" goto compile_error
dumpbin.exe /headers /exports /imports "NVOCombatCore.dll" >dll-details.txt 2>&1
if errorlevel 1 goto inspection_error
echo.
echo BUILD SUCCEEDED. The DLL has not been installed or loaded.
echo Output: "%NVO_BUILD_DIR%\NVOCombatCore.dll"
echo Build log: "%NVO_BUILD_DIR%\build.log"
echo DLL details: "%NVO_BUILD_DIR%\dll-details.txt"
echo Follow START-HERE.html to copy the DLL and perform your load check.
popd
popd
if /I not "%~1"=="--no-pause" pause
exit /b 0

:compile_error
echo.
echo BUILD FAILED. Do not install a DLL from this attempt.
type build.log
echo Send this file: "%NVO_BUILD_DIR%\build.log"
popd
goto failed

:inspection_error
echo.
echo Compilation completed, but DLL inspection failed. Stop before installing.
echo Send "%NVO_BUILD_DIR%\dll-details.txt" and build.log from the same folder.
popd
goto failed

:toolchain_error
echo.
echo The C++ build environment could not be initialized.
type "%NVO_BUILD_DIR%\toolchain.log"
echo Send this file: "%NVO_BUILD_DIR%\toolchain.log"
goto failed

:missing_tools
echo.
echo Visual Studio 2022 or 2026 C++ build tools were not found.
echo Open START-HERE.html and install the Desktop development with C++ workload.
echo Include MSVC x64/x86 build tools and a Windows SDK, then run BUILD.cmd again.
echo No files were downloaded or installed by this helper.
goto failed

:folder_error
echo.
echo Cannot create or enter the build folder. Extract the whole packet to a writable folder.
goto failed

:failed
popd
if /I not "%~1"=="--no-pause" pause
exit /b 1
