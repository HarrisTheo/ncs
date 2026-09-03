from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).parents[1] / "app.py"


def test_initial_ui_has_required_controls_and_notice() -> None:
    app = AppTest.from_file(APP_PATH).run(timeout=10)

    assert not app.exception
    assert app.title[0].value == "AI Incident Triage & Investigation Copilot"
    assert app.text_area[0].label == "Incident description"
    assert app.button[0].label == "Analyze"
    assert any(
        "fictional policies" in info.value.lower()
        and "human judgement" in info.value.lower()
        for info in app.info
    )


def test_empty_submission_shows_clear_failure_without_inference() -> None:
    app = AppTest.from_file(APP_PATH).run(timeout=10)
    app.button[0].click().run(timeout=10)

    assert not app.exception
    assert any("empty input" in error.value.lower() for error in app.error)
