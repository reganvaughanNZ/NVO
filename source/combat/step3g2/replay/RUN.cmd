@echo off
call "C:\Program Files\Microsoft Visual Studio\18\Community\Common7\Tools\VsDevCmd.bat" -no_logo -arch=x86 -host_arch=x64 >toolchain.log 2>&1
if errorlevel 1 exit /b 1
cl /nologo /MT /O2 /std:c++17 /EHsc /W4 /WX /permissive- /I"C:\Users\regan\Documents\ChatGPT\NVO\native\NVOCombatCore\include" /I"C:\Users\regan\Documents\ChatGPT\NVO\native\NVOCombatCore\src" replay.cpp /Fe:replay.exe >build.log 2>&1
if errorlevel 1 exit /b 1
replay.exe >results.jsonl
exit /b %ERRORLEVEL%
