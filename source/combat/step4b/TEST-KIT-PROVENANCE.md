# 4B test helper provenance

Forms read directly from installed FalloutNV.esm: Combat Armor00020420 (base health400, BMDT04); Combat Helmet00020426 (base health50, BMDT00000602); 9mm Pistol000E3778; standard9mm0008ED03; normal CrBloatFly0009189C. Raw rows are retained in TEST-FORMS.jsonl.

Local xNVSE source Commands_Inventory.cpp:2261-2277 verifies SetEquippedCurrentHealth takes current health followed by slot index. GameForms.h:909-920 defines body index2 and hair index1 (occupied by this helmet). Helpers use those indices and explicitly selected target context. Gameplay execution remains for the user; no success is inferred from generating these files.
