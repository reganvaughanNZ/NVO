@echo off
setlocal
cd /d "%~dp0"
if not exist out mkdir out
call "C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >out\coverage-integration-toolchain.log 2>&1
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- /DWIN32_LEAN_AND_MEAN /DNOMINMAX /I"..\include" /I"..\..\NVOCombatModel" ArmourCoverageIntegrationTests.cpp "..\src\ArmourOrigin.cpp" "..\src\ArmourCoverageConfig.cpp" "..\src\ArmourCoverage.cpp" "..\src\ArmourSnapshotReader.cpp" "..\..\NVOCombatModel\CoverageProfiles.cpp" /Foout\ /Feout\ArmourCoverageIntegrationTests.exe >out\coverage-integration-build.log 2>&1
if errorlevel 1 exit /b 1
out\ArmourCoverageIntegrationTests.exe >out\coverage-integration-results.txt
exit /b %ERRORLEVEL%
