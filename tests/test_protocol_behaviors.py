from rt_utils import TaskSpec, simulate_uniprocessor

def _task(task_id: int, period: int, computation: int, resources: dict[str, int], phase: int = 0) -> TaskSpec:
    return TaskSpec(
        task_id=task_id,
        phase=phase,
        period=period,
        computation=computation,
        deadline=period,
        resources=resources,
    )

def _count_blocked(segments: list[dict[str, object]]) -> int:
    return sum(1 for s in segments if s.get("phase") == "Blocked")

def test_none_protocol_can_block_on_resource_contention() -> None:
    tasks = [
        _task(1, period=10, computation=4, resources={"A": 3}, phase=0),
        _task(2, period=5, computation=2, resources={"A": 1}, phase=1),
    ]
    segments = simulate_uniprocessor(tasks, horizon=8, algorithm="RM", protocol="None", resource_order="Resources then CPU")
    assert _count_blocked(segments) >= 1

def test_npp_marks_non_preemptive_resource_phase_as_resource() -> None:
    tasks = [
        _task(1, period=8, computation=4, resources={"A": 2}, phase=0),
        _task(2, period=8, computation=2, resources={}, phase=1),
    ]
    segments = simulate_uniprocessor(tasks, horizon=8, algorithm="RM", protocol="NPP", resource_order="Resources then CPU")
    resource_ticks = [s for s in segments if s.get("task") == "T1" and s.get("phase") == "Resource"]
    assert len(resource_ticks) >= 1

def test_pcp_executes_resource_phases_without_crashing() -> None:
    tasks = [
        _task(1, period=10, computation=4, resources={"A": 3}, phase=0),
        _task(2, period=5, computation=2, resources={"A": 1}, phase=1),
    ]
    segments = simulate_uniprocessor(tasks, horizon=8, algorithm="DM", protocol="PCP", resource_order="Resources then CPU")
    assert len(segments) > 0
    assert any(s.get("phase") == "Resource" for s in segments)

def test_pip_runs_without_crashing_and_emits_segments() -> None:
    tasks = [
        _task(1, period=7, computation=4, resources={"A": 2}, phase=0),
        _task(2, period=7, computation=2, resources={"A": 1}, phase=1),
    ]
    segments = simulate_uniprocessor(tasks, horizon=9, algorithm="RM", protocol="PIP", resource_order="Resources then CPU")
    assert len(segments) > 0


def test_nested_resource_access_holds_earlier_resources_across_later_phases() -> None:
    tasks = [
        _task(1, period=10, computation=4, resources={"A": 1, "B": 2}, phase=0),
        _task(2, period=5, computation=1, resources={"A": 1}, phase=1),
    ]

    non_nested = simulate_uniprocessor(
        tasks,
        horizon=6,
        algorithm="RM",
        protocol="None",
        resource_order="Resources then CPU",
        resource_access_mode="Non-nested",
    )
    nested = simulate_uniprocessor(
        tasks,
        horizon=6,
        algorithm="RM",
        protocol="None",
        resource_order="Resources then CPU",
        resource_access_mode="Nested",
    )

    assert _count_blocked(nested) > _count_blocked(non_nested)