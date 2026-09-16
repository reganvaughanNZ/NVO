# Step 4B reader test matrix

+The 452-check x86 harness exercises the production `ArmourSnapshotReader.cpp` directly. Major groups:

+- full and explicit condition; zero-condition retained; all raw ARMO fields including 32-bit high flags; exact instance token;
+- body plus helmet; same base form on distinct exact instances; empty and no-Worn/baked-model cases never become verified bare;
+- missing/duplicate ContainerChanges, owner mismatch, presence mismatches, null lists, unsupported worn types, and WornLeft rejection;
+- actor, entry, instance, and extra cycles/aliases, including a shared ExtraWorn across distinct instances;
+- low, misaligned, and unreadable pointers plus failure injection at every guarded read;
+- invalid health, base health, mask, DT, and nonfinite values;
+- exact and cap-plus-one traversal tests, including 8,192 total instance extras and 32 output rows;
+- source-memory canary proving no mutation;
+- mutations between passes to condition, instance identity, and armour fields;
+- Creature and target-identity rejection;
+- every semantic and gameplay-authority flag remains false.
