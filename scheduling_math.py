from __future__ import annotations
import math
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from rt_utils import TaskSpec

def utilisation(tasks: List["TaskSpec"]) -> float:
    if not tasks:
        return 0.0
    return sum(task.computation / task.period for task in tasks)

def density(tasks: List["TaskSpec"]) -> float:
    if not tasks:
        return 0.0
    return sum(task.computation / min(task.deadline, task.period) for task in tasks)

def rm_bound(task_count: int) -> float:
    if task_count <= 0:
        return 1.0
    return task_count * (2 ** (1.0 / task_count) - 1.0)

def compute_hyperperiod(periods: List[int]) -> int:
    def lcm(a: int, b: int) -> int:
        return abs(a * b) // math.gcd(a, b)

    hyper = 1
    for period in periods:
        if period <= 0:
            raise ValueError("Periods must be positive integers")
        hyper = lcm(hyper, period)
    return hyper