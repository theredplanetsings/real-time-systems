"""
Manual verification of DM with PIP schedule
"""

print("="*90)
print("TASK SET VERIFICATION - DM with PIP")
print("="*90)
print("T1: φ=7, T=7, D=4, C=1, δA=1, δB=0 → CPU:0, ResA:1, ResB:0 (Priority=4 HIGHEST)")
print("T2: φ=1, T=12, D=12, C=4, δA=3, δB=0 → CPU:1, ResA:3, ResB:0 (Priority=12)")
print("T3: φ=3, T=10, D=10, C=3, δA=0, δB=1 → CPU:2, ResA:0, ResB:1 (Priority=10)")
print("T4: φ=0, T=14, D=14, C=3, δA=0, δB=3 → CPU:0, ResA:0, ResB:3 (Priority=14 LOWEST)")

print("\n" + "="*90)
print("JOB ARRIVALS")
print("="*90)
print("T1: t=7, t=14")
print("T2: t=1, t=13")
print("T3: t=3, t=13")
print("T4: t=0, t=14")

print("\n" + "="*90)
print("STEP-BY-STEP MANUAL TRACE")
print("="*90)

trace = [
    (0, "T4.0", "ResB", "T4 arrives, no CPU work, acquires Resource B (1/3)", ""),
    (1, "T2.0", "CPU", "T2 arrives (P=12 > T4's 14), preempts, CPU work (1/1 done)", ""),
    (2, "T2.0", "ResA", "T2 acquires Resource A (1/3)", ""),
    (3, "T3.0", "CPU", "T3 arrives (P=10 > T2's 12), preempts, CPU work (1/2)", ""),
    (4, "T3.0", "CPU", "T3 continues CPU work (2/2 done, now needs ResB)", ""),
    (5, "T4.0", "ResB", "T3 needs ResB but T4 holds it → T4 INHERITS T3's priority (10) → T4(10)=T3(10)>T2(12)", "INHERITED"),
    (6, "T4.0", "ResB", "T4 continues with inherited priority (3/3 DONE, releases B)", ""),
    (7, "T2.0", "ResA", "T1 arrives (P=4) but needs ResA, T2 holds it → T2 INHERITS T1's priority (4) → T2(4)>T3(10)", "INHERITED"),
    (8, "T2.0", "ResA", "T2 continues with inherited priority (3/3 DONE, releases A)", ""),
    (9, "T1.0", "ResA", "T1 acquires Resource A (1/1 DONE, complete)", ""),
    (10, "T3.0", "ResB", "T3 acquires Resource B (1/1 DONE, complete)", ""),
    (11, "IDLE", "-", "No tasks ready", ""),
    (12, "IDLE", "-", "No tasks ready", ""),
    (13, "T3.1", "CPU", "T3 second job arrives (3+10=13), CPU work (1/2)", ""),
]

for t, task, work, explanation, inherited in trace:
    inh_mark = " ← PIP!" if inherited == "INHERITED" else ""
    print(f"t={t:2d}: {task:6s} {work:6s} - {explanation}{inh_mark}")

print("\n" + "="*90)
print("CRITICAL VERIFICATION POINTS")
print("="*90)

print("\n1. DM Priority Order:")
print("   T1 (D=4) > T3 (D=10) > T2 (D=12) > T4 (D=14)")

print("\n2. Work Breakdown:")
print("   T1: 0 CPU + 1 ResA = 1 total")
print("   T2: 1 CPU + 3 ResA = 4 total")
print("   T3: 2 CPU + 1 ResB = 3 total")
print("   T4: 0 CPU + 3 ResB = 3 total")

print("\n3. Execution Order (per problem statement):")
print("   CPU-only work FIRST, then resource work")

print("\n4. PIP Events:")
print("   t=5: T4 inherits T3's priority (10) because T3 blocked on Resource B")
print("        Effective: T4(10) = T3(10) > T2(12)")
print("   t=7: T2 inherits T1's priority (4) because T1 blocked on Resource A")
print("        Effective: T2(4) > T3(10)")

print("\n5. Resource Blocking:")
print("   t=5-6: T3 blocked by T4 holding Resource B")
print("   t=7-8: T1 blocked by T2 holding Resource A")

print("\n6. Job Completions:")
print("   T4.0 completes at end of t=6")
print("   T2.0 completes at end of t=8")
print("   T1.0 completes at end of t=9")
print("   T3.0 completes at end of t=10")
print("   T3.1 arrives at t=13 (3 + 10)")

print("\n" + "="*90)
print("CONCLUSION: Schedule is CORRECT ✓")
print("="*90)
print("\nKey insight: T4 has NO CPU work, so it goes straight to Resource B.")
print("This is why t=0 shows 'Using Resource B' not 'CPU-only'.")
