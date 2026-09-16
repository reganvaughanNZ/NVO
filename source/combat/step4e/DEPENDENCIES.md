# Dependencies and donor boundary

## This packet

New runtime dependencies: none. No new DLL, startup script, game-side framework or plugin record is supplied. The existing NVOCombatCore native327 reads the generated4D TSV. Its existing extender requirements are unchanged.

Authoring tool: Python with its standard library and the included NVO source modules. Python is used outside the game to prepare the file; players do not need Python to use a generated file. The optional standalone C++ verification uses the installed MSVC x86 tools. Neither tool is run by New Vegas.

The resolver is original NVO code. KEYWORDS contributes the general idea of explicit shared classifications. We have not copied JIP's internal container, linked JIP source, added its private layouts to the native plugin, or reimplemented its runtime keyword registry.

## What a later live adapter would mean

JIP's supplied source implements AssignKeyword, HasKeyword and GetKeywordForms as script commands over its own registry. The game already uses JIP as a dependency. A future adapter using those commands would still rely on the installed JIP interface and verified load order/timing; copying a function body would not make the original registry available to NVO.

The separate KEYWORDS framework loads keyword assignments from configuration. Consuming that framework's files or startup behaviour would add a framework-file dependency even if no additional DLL were necessary. That is optional future work and is not claimed by4E. Native access must use a reviewed supported interface rather than guessed private addresses. Runtime-mutating tags would also need explicit cache invalidation.

We can later translate reviewed external assignments into this exact-record authoring format without requiring a live framework. Such an importer would need to resolve its identifiers and report ambiguity; it is not implemented here.

## References

- KEYWORDS by JazzIsParis and Xilandro: https://www.nexusmods.com/newvegas/mods/83088 . Concept/reference only; no files redistributed in4E.
- Local JIP source: functions_jip/jip_fn_miscellaneous.h, AssignKeywordRecourse and Cmd_AssignKeyword_Execute / Cmd_HasKeyword_Execute / Cmd_GetKeywordForms_Execute. The inspected file hash is recorded in Evidence/VERIFICATION.json. Code was read to establish ownership/interface boundaries; it was not copied into4E.
- The local KEYWORDS1.01 archive remains a donor reference. No archive contents were imported or inspected for this packet; framework details beyond the previously read author documentation are not asserted.

NVO-owned authoring tags are not automatically shared with other mods. Existing game-mod behaviour, installed donor licensing, or public API compatibility is not changed by this offline compiler.
