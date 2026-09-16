from pathlib import Path
root=Path(__file__).resolve().parents[1]
native=root/'native/NVOCombatCore'
p=native/'src/Plugin.cpp'
s=p.read_text().replace('kPluginVersion = 326; // 0.3.26, packet 4B raw armour snapshot reader','kPluginVersion = 327; // 0.3.27, packet 4D origin and coverage diagnostics')
s=s.replace('0.3.26','0.3.27').replace('phase=4B |','phase=4D | coverage_classification_pending=1 |')
p.write_text(s,encoding='utf-8')
p=native/'BUILD.cmd';s=p.read_text()
if 'ArmourOrigin.cpp' not in s:
    s=s.replace('/I"%NVO_PROJECT_DIR%\\include"','/I"%NVO_PROJECT_DIR%\\include" /I"%NVO_PROJECT_DIR%\\..\\NVOCombatModel"')
    s=s.replace('"%NVO_PROJECT_DIR%\\src\\ArmourSnapshot.cpp"','"%NVO_PROJECT_DIR%\\src\\ArmourSnapshot.cpp" "%NVO_PROJECT_DIR%\\src\\ArmourOrigin.cpp" "%NVO_PROJECT_DIR%\\src\\ArmourCoverageConfig.cpp" "%NVO_PROJECT_DIR%\\src\\ArmourCoverage.cpp" "%NVO_PROJECT_DIR%\\..\\NVOCombatModel\\CoverageProfiles.cpp"')
p.write_text(s,encoding='utf-8')
p=native/'CMakeLists.txt';s=p.read_text().replace('VERSION 0.3.26','VERSION 0.3.27')
if 'src/ArmourOrigin.cpp' not in s:
    s=s.replace('src/ArmourSnapshot.cpp','src/ArmourSnapshot.cpp src/ArmourOrigin.cpp src/ArmourCoverageConfig.cpp src/ArmourCoverage.cpp ../NVOCombatModel/CoverageProfiles.cpp')
    s=s.replace('PRIVATE include)','PRIVATE include ../NVOCombatModel)')
p.write_text(s,encoding='utf-8')
print('Prepared native327 build inputs; no installation.')
