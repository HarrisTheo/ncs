from pathlib import Path

from evals import run_eval as runner


def test_loads_versioned_evaluation_cases() -> None:
    cases = runner.load_cases(Path(__file__).parents[1] / "evals" / "cases.json")

    assert len(cases) == 12
    assert len({case["id"] for case in cases}) == 12


def test_percentage_handles_empty_denominator() -> None:
    assert runner._percentage(0, 0) == "n/a"
    assert runner._percentage(3, 4) == "75.0%"
