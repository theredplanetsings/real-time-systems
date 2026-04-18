from rt_utils import TaskSpec, family_names, rm_bound, schedulability_summary, variants_for_family


def _task(task_id: int, period: int, computation: int, deadline: int | None = None) -> TaskSpec:
    return TaskSpec(
        task_id=task_id,
        phase=0,
        period=period,
        computation=computation,
        deadline=deadline if deadline is not None else period,
    )


def test_edf_passes_when_density_at_most_one() -> None:
    tasks = [_task(1, 5, 1), _task(2, 10, 2)]
    result = schedulability_summary(tasks, "EDF")
    assert result["status"] == "pass"


def test_edf_warns_when_density_exceeds_one() -> None:
    tasks = [_task(1, 4, 3), _task(2, 5, 3)]
    result = schedulability_summary(tasks, "EDF")
    assert result["status"] == "warn"
    assert result["metric"] == "Density"


def test_rm_bound_matches_known_value_for_three_tasks() -> None:
    assert rm_bound(3) == 3 * (2 ** (1.0 / 3) - 1.0)


def test_rm_warns_over_bound() -> None:
    tasks = [_task(1, 3, 1), _task(2, 4, 2), _task(3, 6, 3)]
    result = schedulability_summary(tasks, "RM")
    assert result["status"] == "warn"


def test_global_edf_checks_processor_density() -> None:
    tasks = [_task(1, 4, 2), _task(2, 5, 2), _task(3, 10, 2)]
    ok = schedulability_summary(tasks, "Global EDF", processors=2)
    bad = schedulability_summary(tasks, "Global EDF", processors=1)
    assert ok["status"] == "pass"
    assert bad["status"] == "warn"


def test_global_edf_normalizes_invalid_processor_count() -> None:
    tasks = [_task(1, 4, 2), _task(2, 5, 2), _task(3, 10, 2)]
    result = schedulability_summary(tasks, "Global EDF", processors=0)
    assert result["status"] == "warn"


def test_dm_uses_density_sufficient_check() -> None:
    tasks = [_task(1, 4, 3), _task(2, 6, 3)]
    result = schedulability_summary(tasks, "DM")
    assert result["status"] == "warn"


def test_algorithm_family_names_are_sorted() -> None:
    names = family_names()
    assert names == sorted(names)


def test_variant_names_are_sorted_for_family() -> None:
    names = variants_for_family("RM")
    assert names == sorted(names)
