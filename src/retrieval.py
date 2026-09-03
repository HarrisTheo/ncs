"""Deterministic retrieval over the local Markdown policy corpus."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


_H1_PATTERN = re.compile(r"^#\s+(.+?)\s*$")
_H2_PATTERN = re.compile(r"^##\s+(.+?)\s*$")
_SLUG_PATTERN = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True, slots=True)
class PolicySection:
    """A section loaded from one policy Markdown file."""

    section_id: str
    source: str
    title: str
    heading: str
    text: str


@dataclass(frozen=True, slots=True)
class RetrievalResult:
    """A ranked policy section and its cosine-similarity score."""

    section: PolicySection
    score: float


def load_policy_sections(policy_directory: str | Path) -> list[PolicySection]:
    """Load H2 sections from policy Markdown files in deterministic order.

    A missing or empty directory produces an empty list. ``README.md`` is
    excluded because it documents the corpus rather than defining policy.
    """

    directory = Path(policy_directory)
    if not directory.is_dir():
        return []

    sections: list[PolicySection] = []
    for path in sorted(directory.glob("*.md"), key=lambda item: item.name.casefold()):
        if path.name.casefold() == "readme.md":
            continue
        sections.extend(_parse_policy(path))
    return sections


def retrieve_policy_sections(
    incident_description: str,
    policy_directory: str | Path,
    *,
    limit: int = 3,
) -> list[RetrievalResult]:
    """Return the most relevant policy sections for an incident description.

    The small corpus is indexed in memory on each call. Results with zero
    similarity are omitted so unrelated input is not presented as grounded.
    """

    if limit < 1:
        raise ValueError("limit must be at least 1")

    query = incident_description.strip()
    if not query:
        return []

    sections = load_policy_sections(policy_directory)
    if not sections:
        return []

    searchable_text = [
        f"{section.title}\n{section.heading}\n{section.text}" for section in sections
    ]
    vectorizer = TfidfVectorizer(
        lowercase=True,
        stop_words="english",
        ngram_range=(1, 2),
        sublinear_tf=True,
    )

    try:
        section_vectors = vectorizer.fit_transform(searchable_text)
    except ValueError:
        # scikit-learn raises when the corpus has no usable vocabulary.
        return []

    query_vector = vectorizer.transform([query])
    scores = cosine_similarity(query_vector, section_vectors).ravel()

    ranked = sorted(
        zip(sections, scores, strict=True),
        key=lambda item: (-float(item[1]), item[0].source, item[0].section_id),
    )
    return [
        RetrievalResult(section=section, score=float(score))
        for section, score in ranked[:limit]
        if score > 0
    ]


def _parse_policy(path: Path) -> list[PolicySection]:
    content = path.read_text(encoding="utf-8")
    title = path.stem.replace("-", " ").title()
    current_heading: str | None = None
    current_lines: list[str] = []
    parsed_sections: list[tuple[str, str]] = []

    for line in content.splitlines():
        h1_match = _H1_PATTERN.match(line)
        if h1_match and current_heading is None:
            title = h1_match.group(1).strip()
            continue

        h2_match = _H2_PATTERN.match(line)
        if h2_match:
            if current_heading is not None:
                _append_section(parsed_sections, current_heading, current_lines)
            current_heading = h2_match.group(1).strip()
            current_lines = []
            continue

        if current_heading is not None:
            current_lines.append(line)

    if current_heading is not None:
        _append_section(parsed_sections, current_heading, current_lines)

    slug_counts: dict[str, int] = {}
    sections: list[PolicySection] = []
    for heading, text in parsed_sections:
        base_slug = _slugify(heading)
        slug_counts[base_slug] = slug_counts.get(base_slug, 0) + 1
        suffix = "" if slug_counts[base_slug] == 1 else f"-{slug_counts[base_slug]}"
        sections.append(
            PolicySection(
                section_id=f"{path.stem}#{base_slug}{suffix}",
                source=path.name,
                title=title,
                heading=heading,
                text=text,
            )
        )
    return sections


def _append_section(
    sections: list[tuple[str, str]], heading: str, lines: list[str]
) -> None:
    text = "\n".join(lines).strip()
    if text:
        sections.append((heading, text))


def _slugify(value: str) -> str:
    slug = _SLUG_PATTERN.sub("-", value.casefold()).strip("-")
    return slug or "section"
