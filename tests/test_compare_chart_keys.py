from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def _assert_clean_run(app: AppTest) -> None:
    assert len(app.exception) == 0
    assert len(app.error) == 0


def test_compare_mode_run_compare_is_stable_across_reruns() -> None:
    app = AppTest.from_file(str(ROOT / "pages/02_Compare_Mode.py"))
    app.run(timeout=30)

    run_compare = next(button for button in app.button if button.label == "Run Compare")
    run_compare.click().run(timeout=30)
    _assert_clean_run(app)

    # Re-run to guard against duplicate element IDs when chart content is repeated.
    run_compare = next(button for button in app.button if button.label == "Run Compare")
    run_compare.click().run(timeout=30)
    _assert_clean_run(app)
