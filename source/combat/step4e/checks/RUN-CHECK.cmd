@echo off
setlocal
cd /d "%~dp0"
if not exist out mkdir out
set "NVO_CHECK_SOURCE=%~dp0..\Source"
if not exist "%NVO_CHECK_SOURCE%\NVOCombatCore\include\ArmourCoverageConfig.hpp" set "NVO_CHECK_SOURCE=%~dp0..\..\..\..\native"
call "C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >out\toolchain.log 2>&1
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- /DWIN32_LEAN_AND_MEAN /DNOMINMAX /I"%NVO_CHECK_SOURCE%\NVOCombatCore\include" /I"%NVO_CHECK_SOURCE%\NVOCombatModel" KeywordExportCheck.cpp "%NVO_CHECK_SOURCE%\NVOCombatCore\src\ArmourCoverageConfig.cpp" "%NVO_CHECK_SOURCE%\NVOCombatModel\CoverageProfiles.cpp" /Foout\ /Feout\KeywordExportCheck.exe >out\build.log 2>&1
if errorlevel 1 exit /b 1
out\KeywordExportCheck.exe "..\generated\NVOArmourCoverage.tsv" "SYNTHETIC-ONLY.tsv" >out\results.txt
exit /b %ERRORLEVEL%
