from __future__ import annotations
import math
from typing import TYPE_CHECKING, Iterable, List

if TYPE_CHECKING:
    from rt_utils import TaskSpec

def _validate_positive(value: int, field_name: str) -> None:
    if value <= 0:
        raise ValueError(f"Task {field_name} must be a positive integer")

def utilisation(tasks: List["TaskSpec"]) -> float:
    if not tasks:
        return 0.0
    for task in tasks:
        _validate_positive(task.computation, "computation")
        _validate_positive(task.period, "period")
    return sum(task.computation / task.period for task in tasks)

def density(tasks: List["TaskSpec"]) -> float:
    if not tasks:
        return 0.0
    for task in tasks:
        _validate_positive(task.computation, "computation")
        _validate_positive(task.period, "period")
        _validate_positive(task.deadline, "deadline")
    return sum(task.computation / min(task.deadline, task.period) for task in tasks)

def rm_bound(task_count: int) -> float:
    if task_count <= 0:
        return 1.0
    return task_count * (2 ** (1.0 / task_count) - 1.0)

def compute_hyperperiod(periods: Iterable[int]) -> int:
    def lcm(a: int, b: int) -> int:
        return abs(a * b) // math.gcd(a, b)

    hyper = 1
    for period in periods:
        if period <= 0:
            raise ValueError("Periods must be positive integers")
        hyper = lcm(hyper, period)
    return hyper