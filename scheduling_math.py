"""Scheduling mathematics and feasibility analysis helpers.

This module provides core mathematical functions used in real-time scheduling:
- Utilisation and density calculations for schedulability bounds
- Rate Monotonic (RM) scheduling utilisation bounds (Liu & Layland)
- Hyperperiod (LCM) computation for periodic task sets
- Input validation for task parameters

Functions in this module support both uniprocessor and multiprocessor analyses
across various scheduling algorithms (EDF, RM, DM, etc.).
"""
from __future__ import annotations
import math
from typing import TYPE_CHECKING, Iterable, List

if TYPE_CHECKING:
    from rt_utils import TaskSpec

def _validate_positive(value: int, field_name: str) -> None:
    """Validate that a value is a positive integer.
    
    Args:
        value: The value to validate.
        field_name: The name of the field (for error messages).
    
    Raises:
        ValueError: If value is not a positive integer or is a boolean.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Task {field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"Task {field_name} must be a positive integer")

def utilisation(tasks: List["TaskSpec"]) -> float:
    """Calculate task set utilisation (sum of computation / period).
    
    Utilisation is the fraction of processor time spent executing tasks.
    For uniprocessor scheduling, U <= 1.0 is necessary for feasibility.
    
    Args:
        tasks: List of TaskSpec objects with computation and period.
    
    Returns:
        float: Sum of (computation / period) for all tasks, or 0.0 if empty.
        
    Raises:
        ValueError: If any task has non-positive or non-integer computation/period.
    """
    if not tasks:
        return 0.0
    for task in tasks:
        _validate_positive(task.computation, "computation")
        _validate_positive(task.period, "period")
    return sum(task.computation / task.period for task in tasks)

def density(tasks: List["TaskSpec"]) -> float:
    """Calculate task set density (sum of computation / min(deadline, period)).
    
    Density is similar to utilisation but uses the minimum of deadline and period.
    For EDF scheduling, density <= 1.0 is sufficient for feasibility on uniprocessor.
    
    Args:
        tasks: List of TaskSpec objects with computation, period, and deadline.
    
    Returns:
        float: Sum of (computation / min(deadline, period)) for all tasks, or 0.0 if empty.
        
    Raises:
        ValueError: If any task has non-positive or non-integer computation/period/deadline.
    """
    if not tasks:
        return 0.0
    for task in tasks:
        _validate_positive(task.computation, "computation")
        _validate_positive(task.period, "period")
        _validate_positive(task.deadline, "deadline")
    return sum(task.computation / min(task.deadline, task.period) for task in tasks)

def rm_bound(task_count: int) -> float:
    """Calculate Liu & Layland's Rate Monotonic (RM) scheduling bound.
    
    For a fixed task set, if utilisation is less than this bound, the task set
    is guaranteed to be schedulable using Rate Monotonic scheduling.
    
    The bound converges to ln(2) ≈ 0.693 as task_count approaches infinity.
    
    Args:
        task_count: Number of tasks in the set.
    
    Returns:
        float: The utilisation bound for RM scheduling, or 1.0 if task_count <= 0.
    """
    if task_count <= 0:
        return 1.0
    return task_count * (2 ** (1.0 / task_count) - 1.0)

def compute_hyperperiod(periods: Iterable[int]) -> int:
    """Calculate the hyperperiod (least common multiple) of task periods.
    
    The hyperperiod is the smallest time interval after which the pattern of
    task releases repeats exactly. All periodic tasks will have completed at
    least one full execution cycle by the end of the hyperperiod.
    
    Args:
        periods: Iterable of positive integers representing task periods.
    
    Returns:
        int: The LCM of all periods.
        
    Raises:
        ValueError: If any period is non-positive or non-integer.
    """
    def lcm(a: int, b: int) -> int:
        return abs(a * b) // math.gcd(a, b)

    hyper = 1
    for period in periods:
        if isinstance(period, bool) or not isinstance(period, int):
            raise ValueError("Periods must be positive integers")
        if period <= 0:
            raise ValueError("Periods must be positive integers")
        hyper = lcm(hyper, period)
    return hyper