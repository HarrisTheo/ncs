from pathlib import Path

import pytest

from src.retrieval import load_policy_sections, retrieve_policy_sections


POLICY_DIRECTORY = Path(__file__).parents[1] / "data" / "policies"


@pytest.mark.parametrize(
    ("incident", "expected_source"),
    [
        (
            "A privileged administrator had a suspicious login from an unusual "
            "country and their MFA was reset.",
            "authentication-security.md",
        ),
        (
            "An account downloaded 4,000 customer records in a large unexplained "
            "export.",
            "data-exfiltration.md",
        ),
        (
            "Endpoint protection detected malware execution, persistence, and a "
            "command-and-control connection.",
            "malware-response.md",
        ),
        (
            "The customer-facing service is down with health-check failures, "
            "timeouts, and elevated errors after a deployment.",
            "service-outage.md",
        ),
    ],
)
def test_retrieves_expected_policy_first(incident: str, expected_source: str) -> None:
    results = retrieve_policy_sections(incident, POLICY_DIRECTORY)

    assert results
    assert results[0].section.source == expected_source
    assert results[0].score > 0


def test_loads_policy_sections_with_unique_stable_ids() -> None:
    sections = load_policy_sections(POLICY_DIRECTORY)
    section_ids = [section.section_id for section in sections]

    assert sections
    assert len(section_ids) == len(set(section_ids))
    assert "README.md" not in {section.source for section in sections}
    assert all("#" in section_id for section_id in section_ids)


def test_results_are_deterministic() -> None:
    incident = "Unusual sign-in followed by an unexpected MFA reset"

    first = retrieve_policy_sections(incident, POLICY_DIRECTORY)
    second = retrieve_policy_sections(incident, POLICY_DIRECTORY)

    assert first == second


def test_empty_policy_directory_returns_no_results(tmp_path: Path) -> None:
    assert load_policy_sections(tmp_path) == []
    assert retrieve_policy_sections("Suspicious login", tmp_path) == []


def test_missing_policy_directory_returns_no_results(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    assert load_policy_sections(missing) == []
    assert retrieve_policy_sections("Malware detected", missing) == []


def test_empty_incident_returns_no_results() -> None:
    assert retrieve_policy_sections("   ", POLICY_DIRECTORY) == []


def test_non_positive_limit_is_rejected() -> None:
    with pytest.raises(ValueError, match="limit must be at least 1"):
        retrieve_policy_sections("Service outage", POLICY_DIRECTORY, limit=0)
