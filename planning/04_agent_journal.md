# Agent Journal

## 2026-09-03 — Environment inspection and project scaffold

### Environment information

- Operating system: macOS 26.6.2, build 25G83.
- Kernel and architecture: Darwin 25.6.0 on `arm64` (Apple Silicon).
- macOS system Python: Python 3.9.6 at `/usr/bin/python3`.
- Additional Homebrew Python interpreters:
  - Python 3.13.9.
  - Python 3.12.12.
  - Python 3.10.16.
- Selected project target: Python 3.12, because it is already available locally and is a conservative modern target for the chosen libraries. The macOS system Python will not be used for the project environment.
- Homebrew 6.0.21 is available.
- Ollama CLI: not installed or not available on `PATH`.
- Ollama application: not present in the standard Applications directory.
- Ollama daemon: not reachable at `127.0.0.1:11434`.
- Ollama model cache: not present; no local models were found.
- Repository branch: `main`.
- Repository contents before this step: planning documents `00_problem.md` through `03_preimplementation_review.md` only.

Environment details are recorded descriptively. Project configuration contains no machine-specific absolute filesystem paths.

### Files created

- `app.py`
- `src/__init__.py`
- `src/schemas.py`
- `src/retrieval.py`
- `src/llm.py`
- `src/prompts.py`
- `src/triage.py`
- `src/reviewer.py`
- `data/policies/README.md`
- `evals/cases.json`
- `evals/run_eval.py`
- `tests/.gitkeep`
- `requirements.txt`
- `.env.example`
- `.gitignore`
- `README.md`
- `planning/04_agent_journal.md`

### Assumptions made

- The requested `src/` layout is a small importable package rather than a nested package under another project name.
- The first implementation will use one incident description field and approximately five curated policy documents.
- TF-IDF retrieval will use scikit-learn and remain entirely in process.
- Ollama will be installed and a model chosen later with the user's approval if a substantial download is required.
- `.env.example` documents local environment values, while `.env` remains untracked. No secret is currently required.
- Tests will be added with implementation; an empty tracked `tests/` directory is sufficient for this scaffold.

### Important decisions

- No packages, applications, or models were installed during environment inspection.
- No model name was guessed or embedded in configuration because no Ollama models are present.
- Python 3.12 is documented as the project target; this avoids relying on the older system Python while using an interpreter that is already installed.
- Dependency ranges are broad major-version constraints rather than a generated lock file. Exact versions should be captured after the first successful environment setup and test run.
- The scaffold contains responsibility-level module docstrings only. No retrieval, inference, validation, reviewer, evaluation, or Streamlit application behavior has been implemented.
- The policy directory contains only a format note, not invented organizational policy content.
- JSON evaluation fixtures start with an empty, versioned case collection.
- The Ollama host example uses loopback and the model value is intentionally blank.

## 2026-09-03 — Fictional policy knowledge base

### Files created

- `data/policies/authentication-security.md`
- `data/policies/account-compromise.md`
- `data/policies/data-exfiltration.md`
- `data/policies/malware-response.md`
- `data/policies/service-outage.md`

### Files updated

- `data/policies/README.md`
- `planning/04_agent_journal.md`

### Assumptions and decisions

- The knowledge base is demonstration content only. Every policy contains an explicit fictional-policy notice and makes no claim about a real organization.
- The five documents use a shared `Low`, `Medium`, `High`, and `Critical` severity vocabulary while retaining incident-specific criteria.
- Each document contains purpose, indicators, severity guidance, recommended actions, and human approval requirements under consistent Markdown headings.
- Documents intentionally contain some cross-domain terms, such as suspicious authentication followed by data access, so later retrieval and grounded multi-policy reasoning can be demonstrated.
- Guidance distinguishes suspicion from confirmation and, for data incidents, distinguishes access, download, transfer, and confirmed disclosure.
- Every recommended action remains subject to a recorded human disposition in the application. Actions that change accounts, sessions, endpoints, services, data flows, or external communications explicitly require authorized human approval.
- No policy action is executable by the copilot.
- File names and headings are designed to support deterministic passage identifiers and citations later; explicit citation IDs were not added to keep the documents readable.
- No LLM, retrieval logic, or application behavior was implemented in this step.

## 2026-09-03 — Policy retrieval layer

### Files changed

- `src/retrieval.py`: implemented Markdown section loading and TF-IDF/cosine ranking.
- `tests/test_retrieval.py`: added retrieval and edge-case unit tests.
- `README.md`: updated implementation status.
- `planning/04_agent_journal.md`: recorded this implementation step.

### Implementation decisions

- Retrieval is independent of prompts, Ollama, triage, and reviewer code.
- The loader reads `.md` files from the supplied directory in case-insensitive filename order and intentionally excludes `README.md`.
- Policies are split on level-two Markdown headings. Preamble metadata is not indexed.
- Stable section identifiers are generated from the source filename and heading. Duplicate heading slugs receive deterministic numeric suffixes.
- Search text combines the policy title, section heading, and section body.
- Ranking uses scikit-learn TF-IDF with English stop words, unigrams and bigrams, sublinear term frequency, and cosine similarity.
- The small corpus is indexed in memory for each retrieval call. This avoids an index abstraction or persistence mechanism; the cost is negligible for five short documents.
- Results are ordered by descending raw score with source filename and section identifier as deterministic tie-breakers.
- The default result limit is three. Zero-score sections are omitted rather than presented as relevant.
- Empty input, a missing directory, an empty directory, or a corpus with no usable vocabulary safely returns no results. A non-positive result limit is rejected.
- Results use small frozen dataclasses containing the complete section, source filename, stable identifier, and cosine-similarity score.
- No LLM, prompt, triage, reviewer, UI, embedding, or vector-database behavior was added.

### Test environment

- Created the ignored local `.venv` with the already available Python 3.12.12 interpreter.
- Installed only the dependencies needed for this layer's tests: scikit-learn 1.9.0 and pytest 9.1.1, plus their transitive dependencies.
- No Ollama software or model was installed.

### Tests executed

Command:

```text
.venv/bin/python -m pytest tests/test_retrieval.py -v
```

Result: **10 passed in 21.55 seconds**.

Covered scenarios:

- Suspicious privileged login and MFA reset retrieves `authentication-security.md` first.
- Large customer-record download retrieves `data-exfiltration.md` first.
- Malware execution and command-and-control activity retrieves `malware-response.md` first.
- Customer-facing outage symptoms retrieve `service-outage.md` first.
- Stable unique identifiers and exclusion of the corpus README.
- Repeatable deterministic results.
- Empty, missing, and invalid-input edge cases.

### Known limitations

- TF-IDF is lexical. It can miss relevant policies when the incident uses terminology absent from the corpus, even if the meaning is similar.
- English stop words and word-based tokenization make the current configuration unsuitable for multilingual incidents without adjustment.
- Each heading is ranked independently, so evidence spread across several sections may receive lower scores and document-level context is not combined.
- Similarity values are relative to this small corpus and are not calibrated probabilities or confidence scores.
- Apart from excluding exact zero scores, there is no tuned relevance threshold. A weak non-zero match may still appear in the top three.
- The parser expects meaningful content under level-two headings and does not implement full Markdown semantics.
- The index is rebuilt for each query. This is intentionally simple for five policies but would be inefficient for a much larger corpus or high query volume.
- Retrieval does not assess policy freshness, authority, conflicts, or access permissions.
- The tests demonstrate representative queries, not comprehensive vocabulary or adversarial retrieval coverage.
