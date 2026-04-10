from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
SMOKE_PAGES = [
    "pages/02_Compare_Mode.py",
    "pages/11_Priority_Inversion.py",
    "pages/16_Mixed_Workload_Analysis.py",
]


def _assert_clean_run(app: AppTest) -> None:
    assert len(app.exception) == 0
    assert len(app.error) == 0


def test_core_pages_render_without_runtime_errors() -> None:
    for relative_path in SMOKE_PAGES:
        app = AppTest.from_file(str(ROOT / relative_path))
        app.run(timeout=30)
        _assert_clean_run(app)
