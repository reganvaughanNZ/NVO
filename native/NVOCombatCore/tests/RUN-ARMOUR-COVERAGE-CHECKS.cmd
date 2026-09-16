@echo off
setlocal
cd /d "%~dp0"
if not exist out mkdir out
call "C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >out\coverage-toolchain.log 2>&1
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- /I"..\include" /I"..\..\NVOCombatModel" ArmourCoverageTests.cpp "..\src\ArmourOrigin.cpp" "..\src\ArmourCoverageConfig.cpp" "..\..\NVOCombatModel\CoverageProfiles.cpp" /Foout\ /Feout\ArmourCoverageTests.exe >out\coverage-build.log 2>&1
if errorlevel 1 exit /b 1
out\ArmourCoverageTests.exe >out\coverage-results.txt
exit /b %ERRORLEVEL%
