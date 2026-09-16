# Step 2 — Background categories

Replace the complete source of the existing `ALTBackgroundMenu` script in GECK with `ALTBackgroundMenu.txt`. Compile/save that script, then save NVO.esm. Keep the existing script name and type.

This source adds Roleplay, Hardcore and Powerful categories and preserves all 58 named backgrounds plus the original Random option. Pages contain at most seven backgrounds. Navigation is mapped explicitly to the donor's unchanged background IDs; neither background form list is reordered.

Selecting a background displays its original description and confirmation. Back returns to its category page. Category navigation only changes menu state. The original start controller still runs character creation and applies the selected background after confirmation.

`ALTStartQ.bCustomMenu` is set to -1 to disable the donor's hover panel, whose button-position lookup would display the wrong description in the categorized menu. Its now-unused `iUI` field holds the return page. No new quest variables or records are needed.

Hardcore is a category label, not an automatic survival-mode switch. Powerful groups origins with existing advantages; it does not grant new bonuses. Equipment, starting levels, locations, original drawbacks and the optional Courier flier system are unchanged.

Status: the user reported successful compilation after the loop, string and negative-argument fixes. This file records the corrected Step 2 version. Step 3 separately replaces its GetFormDescription call with Call NVOStartPreview iButton. Do not paste this earlier snapshot over the later GECK version without applying that Step 3 edit. The user handles GECK compilation, saving and all testing. NVO.esm has not been edited by this source preparation.

References: https://geckwiki.com/index.php/MessageBoxExAlt and https://geckwiki.com/index.php/Ar_List
