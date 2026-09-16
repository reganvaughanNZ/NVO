// Compatibility fingerprints of inspected ITR 2.2.2 functions; no executable bytes.
struct HookSpec { U32 site, rva, originalRva; U64 hash; };
constexpr HookSpec kSpecs[] = {
    {0x0087C4DA,0x34F38,0x7C758,0xB457A4C636F15C31ull},
    {0x0089A738,0x34FB7,0x7C76C,0x3F49B9B662DD8214ull},
    {0x008B91E1,0x35036,0x7C780,0x848654F693A4262Bull},
    {0x009B0503,0x350B5,0x7C794,0x89F6E6CDA121084Cull},
    {0x009C1E96,0x35134,0x7C7A8,0x4C36A5EB7E984F69ull},
    {0x009CBDE8,0x351B3,0x7C7BC,0x685D2761A9143FBCull},
};
constexpr unsigned kRelocations[] = {7,15,21,29,39,55,69,78,92,107};
