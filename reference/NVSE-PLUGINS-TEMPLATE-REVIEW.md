# NVSE-Plugins template reference

User supplied `C:/Users/regan/Desktop/NVO Mod References (Open Source)/NVSE-Plugins-main` during the 3C3 investigation. Reviewed root README and LICENSE plus solution inventory. README identifies FNV 1.4.0.525, NVSE 0.5.1.4, Visual Studio 2022/v143 and normal/lean example projects. It links to the separate xNVSE-Plugins repository. The root LICENSE redirects to Ian Patterson's SDK license, so per-file/SDK notices still need review before copying implementation.

Useful as a reference for exported Query/Load entry points, MSVC project organization and eventual registered script commands. Its command example uses a placeholder opcode base; do not transplant that allocation into a public NVO plugin. NVO currently registers no new script commands and already builds a Win32 DLL with inspected xNVSE public-interface prefixes and explicit version/layout gates.

No source copied, template/example DLL installed, SDK downgraded or project migration performed. It cannot establish the runtime movement/collision semantics being investigated. Retain for future interface work once needed.
