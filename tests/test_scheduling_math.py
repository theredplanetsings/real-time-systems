import pytest

from scheduling_math import compute_hyperperiod


def test_compute_hyperperiod_empty_defaults_to_one() -> None:
    assert compute_hyperperiod([]) == 1


def test_compute_hyperperiod_for_common_periods() -> None:
    assert compute_hyperperiod([4, 6, 10]) == 60


def test_compute_hyperperiod_rejects_non_positive_periods() -> None:
    with pytest.raises(ValueError):
        compute_hyperperiod([5, 0, 10])
    with pytest.raises(ValueError):
        compute_hyperperiod([5, -2, 10])
