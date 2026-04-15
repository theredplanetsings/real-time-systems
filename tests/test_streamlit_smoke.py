from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
SMOKE_PAGES = [
    "pages/00_Algorithm_Explorer.py",
    "pages/01_Task_Set_Builder.py",
    "pages/02_Compare_Mode.py",
    "pages/06_Cyclic_Executive.py",
    "pages/10_Time_Demand.py",
    "pages/11_Priority_Inversion.py",
    "pages/15_Slack_Stealing.py",
    "pages/16_Mixed_Workload_Analysis.py",
    "pages/17_Benchmark_Suite.py",
]


def _assert_clean_run(app: AppTest) -> None:
    assert len(app.exception) == 0
    assert len(app.error) == 0


def test_smoke_page_paths_exist() -> None:
    missing = [relative_path for relative_path in SMOKE_PAGES if not (ROOT / relative_path).exists()]
    assert not missing


def test_core_pages_render_without_runtime_errors() -> None:
    for relative_path in SMOKE_PAGES:
        app = AppTest.from_file(str(ROOT / relative_path))
        app.run(timeout=30)
        _assert_clean_run(app)
