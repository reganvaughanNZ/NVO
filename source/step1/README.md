# Step 1 — NVO filename references

Prepared source only. NVO.esm has not been modified by this preparation step. You handle GECK compilation, saving and testing.

With NVO.esm as the active file in GECK Extender:

1. Open **Gameplay → Edit Scripts** and open the existing `ALTStartQscript`.
2. Replace its complete text with `ALTStartQscript.txt` from this folder and use the script editor's Save command to compile it.
3. Open the existing `ALTQscript`, replace its complete text with `ALTQscript.txt`, and save/compile it.
4. If both compile successfully, save NVO.esm from the main GECK window. If either reports an error, retain the error text before proceeding.

The only intended code change is `AltStart.esm` → `NVO.esm`: one load-order lookup and two mentions in its warning message per script. Existing script names, variables and behavior are preserved. Do not create new scripts or use Recompile All.

The source files were freshly extracted from the on-disk NVO.esm. If you have unsaved edits to either script in GECK, apply the filename replacement to those edits instead of replacing the entire script.

After you compile and save these two scripts, step 1 is complete. Step 2 is organizing the background selection into Roleplay, Hardcore and Powerful categories. It has not been started.
