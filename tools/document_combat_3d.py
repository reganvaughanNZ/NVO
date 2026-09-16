"""Generate packet documentation and a bounded installer from the prior transaction."""
from pathlib import Path
import hashlib, json, html
ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'source/combat/step3d'
PROJECT=ROOT/'native/NVOCombatCore'
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>NVO Combat Packet 3D</title>
<style>body{background:#101713;color:#e6f0e8;font:18px/1.6 system-ui;max-width:850px;margin:45px auto;padding:0 24px}h1{line-height:1.2}button{font:inherit;background:#a9ddaf;border:0;border-radius:6px;padding:12px 22px;cursor:pointer}code{color:#b7e7c0}li{margin-bottom:12px}.box{border:1px solid #497450;border-radius:8px;padding:20px}a{color:#bbe8c2}#status{min-height:1.5em}</style>
<h1>NVO Combat Packet 3D</h1><p><strong>Build311 · Four ordinary weapons · Gameplay check pending</strong></p>
<p>The 9mm Pistol, Hunting Rifle, 9mm Submachine Gun and Service Rifle now have explicit profiles for standard ammunition. The purpose of this check is to verify per-shot selection and the new automatic-fire and5.56 profiles.</p>
<div class="box"><h2>Give yourself the kit</h2><p>Load your test save and wait three seconds. Open the game console, paste this command and press Enter.</p><p><code id="cmd">bat NVOFlightKit</code></p><button id="copy" type="button">Copy kit command</button><p id="status" role="status"></p><p>One of each weapon, 3009mm rounds, 100.308 rounds and2005.56mm rounds. Each run adds another kit.</p></div>
<h2>Your compact check</h2><ol><li>Keep <strong>NVO.esm and NVOFlightPilot.esp active</strong>. Load your prepared save, wait three seconds, then run the kit command. Use the regular weapons and <strong>standard ammunition</strong>.</li><li>Stand well back from a solid target. Outside VATS, fire <strong>one pistol shot, one hunting-rifle shot and one service-rifle shot</strong>, pausing between weapons. Then fire a <strong>short SMG burst of about three rounds</strong>.</li><li><strong>Reload once</strong>, wait three seconds, and run the kit command again if needed. Fire <strong>one Service Rifle shot in VATS at a distant live target</strong>.</li><li>Exit and tell me you finished. I will read the game-root <strong>NVOCombatCore.log</strong>. Wait for review before another launch overwrites it.</li></ol>
<p>God mode is fine. No GECK work, video or extra stress test is needed. If flight reports unavailable or firing fails, stop and report it.</p>
<p>Console batch files use .txt: NVOFlightKit.txt is installed beside FalloutNV.exe. This command runs inside New Vegas.</p>
<p><a href="README.md">Full instructions and reversal</a> · <a href="Installation/IMPLEMENTATION.md">Implementation details</a> · <a href="Installation/INSTALL-3D.md">Installation receipt</a></p>
<script>document.getElementById('copy').onclick=async()=>{const text='bat NVOFlightKit';let ok=false;try{await navigator.clipboard.writeText(text);ok=true}catch(e){const t=document.createElement('textarea');t.value=text;document.body.appendChild(t);t.select();ok=document.execCommand('copy');t.remove()}document.getElementById('status').textContent=ok?'Copied. Paste into the New Vegas console.':'Select and copy the command shown above.'}</script></html>'''
page=page.replace('and5.56','and 5.56').replace('3009mm','300 9mm').replace('100.308','100 .308').replace('and2005.56mm','and 200 5.56mm')
(PACKET/'START-HERE.html').write_text(page,encoding='utf-8')
for name in ('README.md','START-HERE.html'):(PROJECT/name).write_bytes((PACKET/name).read_bytes())
source=(ROOT/'tools/install_combat_3c5.ps1').read_text()
source=source.replace('step3c5','step3d').replace('3C5','3D').replace('version -ne 310','version -ne 311').replace('version=310','version=311')
source=source.replace("@('Data/NVSE/Plugins/NVOCombatCore.dll', 'Data/NVSE/Plugins/NVOCombatCore.pdb')",
    "@('Data/NVSE/Plugins/NVOCombatCore.dll', 'Data/NVSE/Plugins/NVOCombatCore.pdb', 'Data/NVSE/Plugins/NVOFlightPreview.ini', 'Data/NVSE/Plugins/NVOFlightPhysics.ini', 'Data/NVOFlightPilot.esp', 'NVOFlightKit.txt')")
source=source.replace('.Count -ne 2','.Count -ne 6').replace('Exactly two unique','Exactly six unique').replace('Only the two named','Only the six named')
source=source.replace("$row.path -match '\\.(esm|esp|bsa|fos)$'","$row.path -match '\\.(esm|bsa|fos)$'")
source=source.replace('Game plugins/assets/saves must not be changed.','ESMs/assets/saves must not be changed.')
(ROOT/'tools/install_combat_3d.ps1').write_text(source,encoding='utf-8')
donors=Path(r'C:/Users/regan/Desktop/NVO Mod References (Open Source)')
refs=['NVSE-master (1)/NVSE-master/nvse/nvse/PluginAPI.h','NVSE-master (1)/NVSE-master/nvse/nvse/EventManager.h',
      'NVSE-master (1)/NVSE-master/nvse/nvse/EventManager.cpp','JIP-LN-NVSE-main/nvse/GameForms.cpp',
      'JIP-LN-NVSE-main/nvse/GameForms.h','JIP-LN-NVSE-main/nvse/GameData.h','JIP-LN-NVSE-main/nvse/GameProcess.h',
      'ShowOff-NVSE-main/SHOWOFF-NVSE/Events/ShowOffEvents.h']
(PACKET/'SOURCE-PROVENANCE.json').write_text(json.dumps([dict(path=str(donors/ref),sha256=hashlib.sha256((donors/ref).read_bytes()).hexdigest()) for ref in refs],indent=2)+'\n')
print('Wrote packet page, README, source provenance and six-file installer.')
