import pytest

from rt_utils import TaskSpec
from scheduling_math import compute_hyperperiod, density, utilisation


def _task(period: int, computation: int = 1, deadline: int | None = None) -> TaskSpec:
    return TaskSpec(
        task_id=1,
        phase=0,
        period=period,
        computation=computation,
        deadline=period if deadline is None else deadline,
    )


def test_compute_hyperperiod_empty_defaults_to_one() -> None:
    assert compute_hyperperiod([]) == 1


def test_compute_hyperperiod_for_common_periods() -> None:
    assert compute_hyperperiod([4, 6, 10]) == 60


def test_compute_hyperperiod_rejects_non_positive_periods() -> None:
    with pytest.raises(ValueError):
        compute_hyperperiod([5, 0, 10])
    with pytest.raises(ValueError):
        compute_hyperperiod([5, -2, 10])


def test_utilisation_rejects_non_positive_period() -> None:
    with pytest.raises(ValueError):
        utilisation([_task(period=0)])


def test_density_rejects_non_positive_deadline() -> None:
    with pytest.raises(ValueError):
        density([_task(period=5, deadline=0)])
