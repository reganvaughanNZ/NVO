# Newly supplied BALLISTX library - reference review

2026-09-15. Reviewed the newly added `C:/Users/regan/Desktop/NVO Mod References (Open Source)/BALLISTX-main` directory. This is a separate C++17 ballistics/guidance simulation library, not Ravuth's Fallout New Vegas BallistX mod. Its README identifies `kodchhdayininyeri/BALLISTX`; its bundled LICENSE is MIT, copyright 2025 Emir. Keep that provenance separate from the existing Fallout donor and retain its notice if code is later copied.

## Potential use

- `include/utils/integrator.h`: an independently written RK4 position/velocity integrator for a future numerical cross-check. NVO already implements RK4 in `native/NVOCombatCore/src/FlightPhysics.cpp`; replacing it does not address the currently observed controller behavior.
- `src/atmosphere/isa_model.cpp`: later reference for atmosphere and velocity relative to wind. Fixed atmosphere remains the current plan. Do not introduce random turbulence into the current deterministic pilot.
- `src/aerodynamics/drag_model.cpp`: interpolation and configurable curve examples. Its `standard_artillery()` is explicitly an approximation, with 13 points through Mach 3. It is not a replacement for our existing donor G1/G7 tables or verified cartridge data.

## Current relevance and limits

The inspected project contains no matches for NVSE, Fallout or Ravuth in its README, include/src trees or CMakeLists. No ESP, ESM, DLL, SLN or VCXPROJ files were found in the supplied tree. It supplies no evidence for the New Vegas controller callsites, stack layout or collision path we are diagnosing.

Its `docs/gravity_fix_summary.md` concerns gravity omitted from its own Python simulation update. That differs from NVO's captured request already containing a vertical component while the engine's resulting movement omits it. Its negative-Y gravity examples also require coordinate conversion for NVO's negative-Z world gravity; copying example vectors directly would be wrong.

Scope was source inspection, not a full library correctness review. README performance/test claims were not validated. No library code was executed, built, copied into NVO or installed.

## Decision

Keep as a secondary mathematics reference. Continue using the actual Fallout BallistX donor scripts/data already available, including `source/combat/step3b2/timing-investigation/BallistXMain-reference.txt`. No added dependency or plan change is needed. The current checkpoint remains 3C4 / 309: diagnostic accepted, gravity unaccepted, and the guarded controller-vector correction awaits the user's approval before preparation/installation.
