"""Initial one-time 3C2 source migration; later reviewed edits are in the native source. Not a release build tool. No game access."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'native/NVOCombatCore/src/FlightPhysics.cpp'
s=p.read_text()
assert 'BeforeMatrix' in s and 'BeforeAccounting' not in s
s=s.replace('kSite = 0x930255, kOriginal = 0x4B4500', 'kSite = 0x9BF461, kOriginal = 0x9C4E60')
s=s.replace('matrixEntries', 'accountingEntries')
s=s.replace('    bool stopped{}, logged{};', '''    bool stopped{}, logged{}, baselineVerified{}, pending{}, wrote{};
    unsigned verifiedSteps{};
    std::uintptr_t frame{};
    DWORD thread{};
    Vec expected{}, startPos{}, proposedVelocity{};
    double pendingDt{}, pendingBaseline{};''')
s=s.replace('unsigned gMatrixEntries{}, gMoveEntries{}, gEarlyRows{};\nunsigned gBadStack{}, gBadCaller{}, gBadOwnerRead{}, gUntrackedOwner{}, gStoppedOwner{};\nunsigned gMoveBadStack{}, gMoveUntracked{}, gMissingRoute{};',
'''unsigned gMoveEntries{}, gAccountingEntries{}, gMoveUntracked{}, gAccountingUntracked{};
unsigned gMissingRoute{}, gBaselines{}, gVerified{}, gMismatched{}, gUnpaired{};''')
s=s.replace('gOriginalFunction','gOriginalAccounting')
a=s.index('void Summary(');b=s.index('bool Snapshot(',a)
s=s[:a]+'''void Summary(const Track& t, const char* reason) noexcept
{
    if (t.logged) nvo::log::Write("PHYSICS_SHOT session=%u lifetime=%llu reason=%s movement_entries=%u accounting_entries=%u baseline_verified=%u steps=%u verified_steps=%u pending=%u elapsed_s=%.9g speed_mps=%.9g stopped=%u",
        gSession,t.serial,reason,t.movementEntries,t.accountingEntries,t.baselineVerified?1u:0u,t.steps,t.verifiedSteps,t.pending?1u:0u,t.elapsed,Length(t.velocity),t.stopped?1u:0u);
}
void MissingRoute(Track& t, const char* reason) noexcept
{
    if (t.steps || t.missingRouteReported) return;
    t.missingRouteReported=1; ++gMissingRoute;
    if (gMissingRoute<=16) nvo::log::Write("PHYSICS_NO_UPDATE session=%u lifetime=%llu reason=%s movement_entries=%u accounting_entries=%u baseline_verified=%u writes=0",
        gSession,t.serial,reason,t.movementEntries,t.accountingEntries,t.baselineVerified?1u:0u);
}
void Reject(Track& t, const char* reason) noexcept
{
    if (t.stopped) return;
    t.stopped=true; t.pending=false; ++gRejected;
    if (gRejected<=16) nvo::log::Write("PHYSICS_REJECT session=%u lifetime=%llu reason=%s subsequent_engine_movement=unchanged",gSession,t.serial,reason);
}
''' +s[b:]
a=s.index('void Early(');b=s.index('bool Fingerprint(',a)
s=s[:a]+r'''// Engine source direction: Rz(heading at +2C) * Rx(pitch at +24).
// Forward is local +Y; positive pitch points down. Rotation Y is not used by
// this verified matrix pair. Reject nonzero roll rather than generalize it.
struct Rotation {
    double cp{}, sp{}, cy{}, sy{};
    Vec World(Vec v) const noexcept {
        const double y=cp*v.y+sp*v.z, z=-sp*v.y+cp*v.z;
        return {cy*v.x+sy*y,-sy*v.x+cy*y,z};
    }
    Vec Local(Vec v) const noexcept {
        const double x=cy*v.x-sy*v.y, y=sy*v.x+cy*v.y;
        return {x,cp*y-sp*v.z,sp*y+cp*v.z};
    }
};
bool RotationOf(void* owner, Rotation& r, float (&angles)[3]) noexcept
{
    if (!Read(owner,0x24,angles)) return false;
    for (float a:angles) if (!std::isfinite(a) || std::abs(a)>100) return false;
    if (std::abs(angles[1])>0.00001f) return false;
    r={std::cos(angles[0]),std::sin(angles[0]),std::cos(angles[2]),std::sin(angles[2])};
    return true;
}
void __cdecl BeforeMovement(void* owner,float adjustedDt,float* input,std::uintptr_t frame) noexcept
{
    const ErrorGuard error;
    if (!gActive.load(std::memory_order_acquire)) return;
    const Lock lock;
    if (!gActive.load(std::memory_order_relaxed)) return;
    ++gMoveEntries;
    auto* t=Find(owner);
    if (!t) { ++gMoveUntracked; return; }
    ++t->movementEntries;
    if (t->stopped) return;
    if (t->pending) { Reject(*t,"missing_accounting_or_overlapping_call"); return; }
    std::uintptr_t caller{},wrapper{},wrapperCaller{}; void *frameOwner{},*wrapperOwner{};
    float dt{},frameDt{};
    if (frame<0x2C || !OnStack(frame-0x2C,0x44)
        || reinterpret_cast<std::uintptr_t>(input)!=frame+0xC
        || !Read(reinterpret_cast<void*>(frame),4,caller) || caller!=0x9BF35D
        || !Read(reinterpret_cast<void*>(frame),-0x2C,frameOwner) || frameOwner!=owner
        || !Read(reinterpret_cast<void*>(frame),8,frameDt) || frameDt!=adjustedDt
        || !Read(reinterpret_cast<void*>(frame),0,wrapper) || wrapper<0x18 || !OnStack(wrapper-0x18,0x24)
        || !Read(reinterpret_cast<void*>(wrapper),4,wrapperCaller) || (wrapperCaller!=0x9B83EA && wrapperCaller!=0x9B8481)
        || !Read(reinterpret_cast<void*>(wrapper),-0x14,wrapperOwner) || wrapperOwner!=owner
        || !Read(reinterpret_cast<void*>(wrapper),8,dt)) { Reject(*t,"movement_stack_contract"); return; }
    if (!std::isfinite(dt) || dt<0 || dt>0.25f || !std::isfinite(adjustedDt) || adjustedDt<0) { Reject(*t,"unsupported_timestep"); return; }
    if (dt==0) return;
    float local[3]{},life{},distance{},pos[3]{},angles[3]{}; Rotation rotation{};
    if (!Read(input,0,local) || !Read(owner,0x30,pos) || !Snapshot(*t,life,distance)) { Reject(*t,"identity_or_collision_or_layout"); return; }
    for (float v:pos) if (!std::isfinite(v) || std::abs(v)>1e7f) { Reject(*t,"invalid_position"); return; }
    if (!RotationOf(owner,rotation,angles)) { Reject(*t,"unsupported_rotation"); return; }
    if (local[0]!=0 || local[2]!=0 || !std::isfinite(local[1]) || local[1]<=0) { Reject(*t,"unsupported_input_vector"); return; }
    if (life<t->life || distance<t->distance || (life==t->life && distance==t->distance)) { Reject(*t,"duplicate_or_reversed_step"); return; }
    const double baseline=local[1]/(static_cast<double>(dt)*gConfig.units);
    if (!std::isfinite(baseline) || baseline<10 || baseline>gConfig.sound*4.9) { Reject(*t,"unsupported_engine_speed"); return; }
    if (t->baselineVerified && std::abs(baseline/t->baseline-1)>0.001) { Reject(*t,"engine_speed_changed"); return; }
    const Vec world=rotation.World({local[0],local[1],local[2]});
    Vec velocity=t->baselineVerified?t->velocity:Mul(world,1/(dt*gConfig.units));
    const Vec before=velocity;
    Vec displacement=world;
    if (t->baselineVerified) {
        displacement=Mul(Integrate(velocity,dt,t->profile),gConfig.units);
        const Vec replacement=rotation.Local(displacement);
        float values[3]={static_cast<float>(replacement.x),static_cast<float>(replacement.y),static_cast<float>(replacement.z)};
        for (float v:values) if (!std::isfinite(v) || std::abs(v)>1e7f) { Reject(*t,"integration_out_of_range"); return; }
        if (!WriteVector(input,values)) { Reject(*t,"stack_write_failed"); return; }
        ++t->steps; ++gApplied;
    }
    t->pending=true; t->wrote=t->baselineVerified; t->frame=frame; t->thread=GetCurrentThreadId();
    t->expected=displacement; t->proposedVelocity=velocity; t->startPos={pos[0],pos[1],pos[2]};
    t->pendingDt=dt; t->pendingBaseline=baseline; t->life=life; t->distance=distance;
    if (t->logged && t->movementEntries<=kLoggedSteps) nvo::log::Write("PHYSICS_STEP session=%u lifetime=%llu step=%u phase=%s profile=%u dt_s=%.9g movement_dt_s=%.9g speed_before_mps=%.9g speed_after_mps=%.9g vz_before=%.9g vz_after=%.9g world_delta=(%.9g,%.9g,%.9g) pitch=%.9g heading=%.9g argument_write=%u damage_write=0",
        gSession,t->serial,t->steps,t->wrote?"apply":"baseline",t->profile,static_cast<double>(dt),static_cast<double>(adjustedDt),
        Length(before),Length(velocity),before.z,velocity.z,displacement.x,displacement.y,displacement.z,
        static_cast<double>(angles[0]),static_cast<double>(angles[2]),t->wrote?1u:0u);
}
void __cdecl BeforeAccounting(void* owner,const float* delta,U32 accumulate,std::uintptr_t frame) noexcept
{
    const ErrorGuard error;
    if (!gActive.load(std::memory_order_acquire)) return;
    const Lock lock;
    if (!gActive.load(std::memory_order_relaxed)) return;
    ++gAccountingEntries;
    auto* t=Find(owner);
    if (!t) { ++gAccountingUntracked; return; }
    ++t->accountingEntries;
    if (t->stopped) return;
    if (!t->pending) { ++gUnpaired; Reject(*t,"accounting_without_movement"); return; }
    std::uintptr_t caller{}; void* frameOwner{};
    if (t->frame!=frame || t->thread!=GetCurrentThreadId() || frame<0x2C || !OnStack(frame-0x2C,0x44)
        || !OnStack(reinterpret_cast<std::uintptr_t>(delta),12) || accumulate!=1
        || !Read(reinterpret_cast<void*>(frame),4,caller) || caller!=0x9BF35D
        || !Read(reinterpret_cast<void*>(frame),-0x2C,frameOwner) || frameOwner!=owner) { Reject(*t,"accounting_stack_contract"); return; }
    // A collision is not a direction failure. Impact/destruction events retire
    // the track; neither this observer nor the movement hook changes collision data.
    void* contacts{}; unsigned char impacted{};
    if (!Read(owner,0x88,contacts) || !Read(owner,0x90,impacted)) { Reject(*t,"accounting_collision_read"); return; }
    if (contacts || impacted) { t->pending=false; return; }
    float actual[3]{},pos[3]{},life{},distance{};
    if (!Read(delta,0,actual) || !Read(owner,0x30,pos) || !Snapshot(*t,life,distance)) { Reject(*t,"accounting_identity_or_read"); return; }
    for (float v:actual) if (!std::isfinite(v)) { Reject(*t,"accounting_nonfinite"); return; }
    for (float v:pos) if (!std::isfinite(v)) { Reject(*t,"accounting_nonfinite_position"); return; }
    const Vec measured{actual[0],actual[1],actual[2]};
    const double vectorError=Length(Add(measured,Mul(t->expected,-1)));
    const double positionError=Length(Add(Add({pos[0],pos[1],pos[2]},Mul(t->startPos,-1)),Mul(measured,-1)));
    const double coordinate=std::fmax(std::fmax(std::abs(t->startPos.x),std::abs(t->startPos.y)),std::abs(t->startPos.z));
    const double tolerance=0.002+coordinate*0.0000005+Length(t->expected)*0.00002;
    const bool matched=vectorError<=tolerance && positionError<=tolerance;
    if (t->logged && t->accountingEntries<=kLoggedSteps) nvo::log::Write("PHYSICS_ACTUAL session=%u lifetime=%llu step=%u phase=%s matched=%u actual_delta=(%.9g,%.9g,%.9g) vector_error=%.9g position_error=%.9g tolerance=%.9g writes=0",
        gSession,t->serial,t->steps,t->wrote?"apply":"baseline",matched?1u:0u,measured.x,measured.y,measured.z,vectorError,positionError,tolerance);
    t->pending=false;
    if (!matched) { ++gMismatched; Reject(*t,t->wrote?"applied_displacement_mismatch":"baseline_direction_mismatch"); return; }
    t->velocity=t->proposedVelocity; t->baseline=t->pendingBaseline;
    if (t->wrote) { t->elapsed+=t->pendingDt; ++t->verifiedSteps; ++gVerified; }
    else { t->baselineVerified=true; ++gBaselines; }
}
__declspec(naked) void MovementBridge()
{
    __asm {
        pushfd
        pushad
        mov ebx, esp
        sub esp, 528
        and esp, -16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp, 4
        push dword ptr [ebx+8]
        push dword ptr [ebx+44]
        push dword ptr [ebx+40]
        push dword ptr [ebx+24]
        call BeforeMovement
        add esp, 16
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        jmp dword ptr [gOriginalMovement]
    }
}
__declspec(naked) void AccountingBridge()
{
    __asm {
        pushfd
        pushad
        mov ebx, esp
        sub esp, 528
        and esp, -16
        fxsave [esp]
        cld
        fninit
        push 01F80h
        ldmxcsr [esp]
        add esp, 4
        push dword ptr [ebx+8]
        push dword ptr [ebx+52]
        lea eax, [ebx+40]
        push eax
        push dword ptr [ebx+24]
        call BeforeAccounting
        add esp, 16
        fxrstor [esp]
        mov esp, ebx
        popad
        popfd
        jmp dword ptr [gOriginalAccounting]
    }
}

''' + s[b:]
s=s.replace('MatrixBridge','AccountingBridge')
s=s.replace('{0xE8,0xA6,0x42,0xB8,0xFF}', '{0xE8,0xFA,0x59,0x00,0x00}')
s=s.replace('PHYSICS_HOOK_READY matrix_site=00930255 matrix_original=004B4500 movement_checkpoint=009BF411 movement_original=0092F260', 'PHYSICS_HOOK_READY movement_site=009BF411 movement_original=0092F260 accounting_site=009BF461 accounting_original=009C4E60 generic_matrix_hook=0')
s=s.replace('gMatrixEntries=gMoveEntries=gEarlyRows=gBadStack=gBadCaller=gBadOwnerRead=gUntrackedOwner=gStoppedOwner=0;\n    gMoveBadStack=gMoveUntracked=gMissingRoute=0;', 'gMoveEntries=gAccountingEntries=gMoveUntracked=gAccountingUntracked=0;\n    gMissingRoute=gBaselines=gVerified=gMismatched=gUnpaired=0;')
a=s.index('        nvo::log::Write("PHYSICS_ROUTE_SUMMARY');b=s.index('\n    }',a)
s=s[:a]+'''        nvo::log::Write("PHYSICS_ROUTE_SUMMARY session=%u reason=%s move_entries_all=%u move_untracked=%u accounting_entries_all=%u accounting_untracked=%u baselines_verified=%u applied_verified=%u mismatches=%u accounting_unpaired=%u lives_without_update=%u",
            gSession,reason,gMoveEntries,gMoveUntracked,gAccountingEntries,gAccountingUntracked,gBaselines,gVerified,gMismatched,gUnpaired,gMissingRoute);'''+s[b:]
s=s.replace('execution_observed=0 damage_replacement=0', 'baseline_steps_per_lifetime=1 execution_observed=0 damage_replacement=0')
s=s.replace('&& Fingerprint(0x009B8030,0x865,0xA1B80FE6DF917F84ull);', '''&& Fingerprint(0x009B8030,0x865,0xA1B80FE6DF917F84ull)
        && Fingerprint(0x009C4E60,0x5E,0xD82BC9F26A9C40F5ull)
        && Fingerprint(0x00430830,0x11,0x22C5CAF119221249ull)
        && Fingerprint(0x00931D70,0x15,0xB917B8CF60D822D8ull)
        && Fingerprint(0x0080F790,0x18,0x5A6DD9F715394886ull)
        && Fingerprint(0x00524AC0,0x73,0x8502BBFDBBBD29A0ull);''')
p.write_text(s)
for name in ('src/Plugin.cpp','CMakeLists.txt'):
 p=root/'native/NVOCombatCore'/name;s=p.read_text().replace('0.3.6','0.3.7').replace('306','307').replace('3C1','3C2').replace('movement route diagnostics','verified movement argument pilot').replace('movement_route_diagnostics=1','movement_argument_pilot=1');p.write_text(s)
print('Updated physics and version only. No build, game edits or execution.')
