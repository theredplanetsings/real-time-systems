import math
from math import gcd
from functools import reduce

# Task set: (Period, Computation Time)
tasks = [
    (15, 2),  # Task 1
    (15, 5),  # Task 2
    (45, 3)   # Task 3
]

print("=" * 70)
print("CYCLIC EXECUTIVE FRAME SIZE ANALYSIS")
print("=" * 70)
print("\nTask Set:")
for i, (T, C) in enumerate(tasks, 1):
    print(f"  Task {i}: (T={T}, C={C})")
print()

# Part a: Calculate Hyperperiod (LCM of all periods)
def lcm(a, b):
    return abs(a * b) // gcd(a, b)

periods = [T for T, C in tasks]
hyperperiod = reduce(lcm, periods)

print("=" * 70)
print("PART A: HYPERPERIOD")
print("=" * 70)
print(f"\nPeriods: {periods}")
print(f"Hyperperiod H = LCM({', '.join(map(str, periods))}) = {hyperperiod}")
print()

# Part b: Find all valid frame sizes
print("=" * 70)
print("PART B: VALID FRAME SIZES")
print("=" * 70)
print("\nFrame Size Conditions:")
print("  1. f ≥ C_max (frame must accommodate largest task)")
print("  2. f divides H evenly (frames fit into hyperperiod)")
print("  3. 2f - gcd(T_i, f) ≤ T_i for all tasks (timing constraint)")
print()

# Condition 1: f >= C_max
C_max = max(C for T, C in tasks)
print(f"Condition 1: f ≥ C_max = {C_max}")
print()

# Condition 2: Find all divisors of hyperperiod
print(f"Condition 2: f must divide H = {hyperperiod}")
divisors = []
for i in range(1, hyperperiod + 1):
    if hyperperiod % i == 0:
        divisors.append(i)
print(f"Divisors of {hyperperiod}: {divisors}")
print()

# Filter divisors that satisfy condition 1
candidate_frames = [f for f in divisors if f >= C_max]
print(f"Divisors ≥ {C_max}: {candidate_frames}")
print()

# Condition 3: Check timing constraint for each candidate
print("Condition 3: Checking 2f - gcd(T_i, f) ≤ T_i for all tasks")
print("-" * 70)

valid_frames = []

for f in candidate_frames:
    print(f"\nTesting f = {f}:")
    all_satisfied = True
    
    for i, (T, C) in enumerate(tasks, 1):
        g = gcd(T, f)
        left_side = 2 * f - g
        satisfied = left_side <= T
        
        status = "✓" if satisfied else "✗"
        print(f"  Task {i} (T={T:2d}): 2({f}) - gcd({T},{f}) = {2*f} - {g} = {left_side:2d} ≤ {T:2d}  {status}")
        
        if not satisfied:
            all_satisfied = False
    
    if all_satisfied:
        valid_frames.append(f)
        print(f"  → f = {f} is VALID")
    else:
        print(f"  → f = {f} is INVALID")

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print(f"\nHyperperiod: {hyperperiod}")
print(f"Valid Frame Sizes: {valid_frames}")
print()

# Show work summary
print("DETAILED WORK:")
print("-" * 70)
print(f"a) Hyperperiod = LCM(15, 15, 45) = {hyperperiod}")
print()
print(f"b) Frame size conditions:")
print(f"   • Must be ≥ C_max = {C_max}")
print(f"   • Must divide {hyperperiod}")
print(f"   • Candidates: {candidate_frames}")
print()
print("   Testing each candidate:")
for f in candidate_frames:
    if f in valid_frames:
        print(f"   • f = {f}: All conditions satisfied ✓")
    else:
        print(f"   • f = {f}: Failed condition 3 ✗")
print()
print(f"   Valid frame sizes: {valid_frames}")
print("=" * 70)
