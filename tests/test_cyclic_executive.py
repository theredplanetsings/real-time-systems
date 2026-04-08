from rt_utils import TaskSpec, cyclic_executive_frames, cyclic_executive_schedule

def _task(task_id: int, period: int, computation: int, phase: int = 0) -> TaskSpec:
    return TaskSpec(
        task_id=task_id,
        phase=phase,
        period=period,
        computation=computation,
        deadline=period,
    )

def test_cyclic_frames_find_valid_candidates_for_balanced_set() -> None:
    tasks = [_task(1, 4, 1), _task(2, 8, 2), _task(3, 16, 2)]
    hyper, valid_frames = cyclic_executive_frames(tasks)
    assert hyper == 16
    assert len(valid_frames) > 0

def test_cyclic_schedule_stays_within_frame_window() -> None:
    tasks = [_task(1, 4, 1), _task(2, 8, 2)]
    _, valid_frames = cyclic_executive_frames(tasks)
    frame = valid_frames[0]
    segments = cyclic_executive_schedule(tasks, frame)
    assert len(segments) > 0
    for segment in segments:
        assert segment["end"] > segment["start"]
        frame_index = int(segment["lane"].split()[-1]) - 1
        frame_start = frame_index * frame
        frame_end = frame_start + frame
        assert segment["start"] >= frame_start
        assert segment["end"] <= frame_end

def test_cyclic_schedule_segments_have_expected_phase_tag() -> None:
    tasks = [_task(1, 5, 2), _task(2, 10, 2)]
    _, valid_frames = cyclic_executive_frames(tasks)
    if not valid_frames:
        return
    segments = cyclic_executive_schedule(tasks, valid_frames[0])
    assert all(s["phase"] == "Frame" for s in segments)