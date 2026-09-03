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

## 2026-09-03 — Ollama integration preflight

### Environment findings

- The Ollama CLI is not installed or is not available on `PATH`.
- The Ollama desktop application is not present in the standard Applications directory.
- No Ollama Homebrew formula is installed.
- No daemon responded at the configured loopback endpoint.
- No local Ollama model manifests or model cache were found.
- The Python Ollama client is not installed in the project virtual environment.

### Decision

- Local inference cannot be exercised without first installing Ollama and at least one model.
- No Ollama software, Python client, or model was installed.
- No model was selected because there are no installed candidates to inspect and model downloads require prior user approval.
- Provider integration implementation and its unit tests were paused at the explicit pre-installation decision point. No inference call was attempted.

## 2026-09-03 — Ollama installation and provider integration

### Model selected

- Model: `qwen3.5:9b`.
- Installed size: approximately 6.6 GB.
- Parameters: 9.7 billion.
- Quantization: Q4_K_M.
- Advertised maximum context: 262,144 tokens; the application adapter deliberately limits requests to 8,192 tokens.
- Ollama capabilities reported by the local manifest: completion, vision, tools, and thinking. This project uses text completion only, supplies a JSON schema, disables thinking output, and gives the model no tools.

### Why this model was selected

- The 9B-class model is a reasonable quality and memory compromise for the 18 GB Apple Silicon development machine.
- Its 6.6 GB Q4 quantization leaves materially more unified memory for macOS, Ollama runtime overhead, context state, and the Streamlit application than a 17 GB 27B model would.
- It should provide more reliable instruction-following and structured synthesis than the smallest 2B or 4B options while remaining practical for local interactive use.
- Ollama exposes JSON-schema constrained output for this model through the same local chat API used by the adapter.
- The selected model is configurable rather than embedded in application logic. `OLLAMA_MODEL` in `.env.example` records the development default.

### Expected local-model limitations

- Q4 quantization trades some output quality for lower memory use.
- The model can still hallucinate facts, misuse policy passages, or return schema-invalid data; Pydantic validation and visible sources remain necessary.
- Confidence values are model estimates, not calibrated probabilities.
- The 8,192-token application context is intentionally much smaller than the advertised maximum, so excessive policy or incident text must be rejected or truncated deterministically later.
- First-request model loading and CPU/GPU contention may cause noticeable latency.
- A reviewer using the same model can reproduce the triage model's errors and is not independent assurance.
- The model has general learned knowledge that may be outdated or irrelevant; prompts restrict it to supplied incident and policy context, but this restriction is not guaranteed.
- Vision, tool use, and thinking output are unused. The model has no credentials, remediation tools, or operational authority.

### Local software changes

- Installed Ollama 0.33.2 through Homebrew.
- Started the Homebrew Ollama service. It was verified listening on loopback only at `127.0.0.1:11434`.
- Pulled `qwen3.5:9b` through Ollama and verified its digest and local manifest.
- Installed the Ollama Python client 0.6.2 in the ignored project virtual environment.
- The Homebrew Ollama installation also installed its MLX, MLX-C, and Python 3.14 dependencies and upgraded several existing Homebrew libraries. The project remains on its isolated Python 3.12 virtual environment.
- No real inference request was made during installation or unit testing.

### Provider integration

- `src/llm.py` now defines a small provider-neutral `StructuredLLM` protocol and one `OllamaLLM` implementation.
- The model may be supplied directly or through `OLLAMA_MODEL`; an explicit value takes precedence.
- The host may be supplied directly or through `OLLAMA_HOST`, but the MVP rejects non-loopback endpoints.
- Ollama-specific construction, chat calls, options, and exceptions remain inside `src/llm.py`.
- Requests are non-streaming, use temperature zero, cap context at 8,192 tokens by default, disable thinking output, and send the Pydantic JSON schema to Ollama.
- The adapter has explicit configuration, unavailable-service/model, timeout, and malformed-response errors.
- Malformed-response exceptions do not echo raw model output, avoiding accidental leakage into logs or UI errors.
- There is no automatic retry, model download, provider registry, or inference orchestration.

### Files changed

- `src/llm.py`
- `tests/test_llm.py`
- `.env.example`
- `README.md`
- `planning/04_agent_journal.md`

### Tests executed

- Provider unit suite: **27 passed**. These tests use a mock client and make no inference or network calls.
- Full project suite before final documentation verification: **62 passed**.
- Covered model configuration, precedence, loopback enforcement, client construction, deterministic request options, schema passing, connection failure, provider failure, timeout, missing response content, malformed JSON, Pydantic mismatch, non-echoing errors, and the replaceable protocol surface.

## 2026-09-03 — Grounded triage path

### Files changed

- `src/schemas.py`: added bounded `IncidentInput` validation.
- `src/triage.py`: implemented UI-independent triage orchestration and a command-line entry point.
- `tests/test_triage.py`: added deterministic pipeline tests with stub model providers.
- `README.md`: documented the implemented triage status and manual command.
- `planning/04_agent_journal.md`: recorded this implementation and real-model inspection.

### Implemented flow

The implemented flow is:

> incident → Pydantic input validation → TF-IDF retrieval → deterministic policy-context expansion → local structured Ollama inference → Pydantic parsing and validation → citation-membership verification → `IncidentAssessment`

Important decisions:

- Incident descriptions must contain 20 to 5,000 non-whitespace characters.
- Retrieval keeps the existing deterministic top-three section matches and their cosine scores.
- A retrieval probe showed that top sections correctly identify the incident domains but can omit the same documents' recommended-action sections. The context builder therefore expands only the documents represented in the ranked top-three matches and supplies all of their sections to the model.
- Ranked matches and expanded context passages are retained separately in `TriageRun`, so a caller can inspect both what matched and exactly what the model saw.
- Model input is JSON-delimited and includes exact source filenames and section identifiers.
- Every structured policy reference in the assessment is checked against the passages actually supplied to the model. An unknown filename or section ID rejects the assessment.
- Invalid incident input or missing retrieval context stops before inference. There is no synthetic fallback assessment.
- Provider and malformed-response errors remain visible and are not converted into plausible-looking results.
- The command-line entry point prints an auditable JSON artifact and returns a non-zero status with a concise error on failure.
- The reviewer and Streamlit UI remain unimplemented.

### Deterministic tests

The new tests cover:

- Successful grounded orchestration with traceable sources.
- Expansion of matched documents to include recommended actions and human approval requirements.
- Empty, too-short, and oversized incident rejection before inference.
- Empty policy directory failure without a fallback result.
- Rejection of a fabricated structured policy citation.
- Propagation of malformed model-response failure.
- Explicit low-confidence handling of insufficient information.
- Exact source identifiers in the JSON-delimited model context.

Schema and triage focused tests: **35 passed** before the manual inference run.

### Manual local-model test

Input:

> An administrator account logged in from an unusual location, MFA was reset, and approximately 4,000 customer records were downloaded.

Model: `qwen3.5:9b`, with thinking disabled and structured output validated as `IncidentAssessment`.

Ranked retrieval matches:

1. `data-exfiltration#severity-guidance` from `data-exfiltration.md`, score `0.1405`.
2. `authentication-security#indicators` from `authentication-security.md`, score `0.1369`.
3. `authentication-security#human-approval-requirements` from `authentication-security.md`, score `0.0889`.

The grounded context contained all five sections from `data-exfiltration.md` and all five sections from `authentication-security.md`. It did not contain `account-compromise.md`.

Validated model assessment:

- Category: `data_exfiltration`.
- Severity: `high`.
- Confidence: `0.9`.
- Evidence: unusual administrator login, MFA reset, and download of approximately 4,000 customer records.
- Policies cited: data-exfiltration severity and indicators; authentication-security severity.
- Recommendations: preserve access/export/transfer audit evidence, and recommend session revocation or temporary access restriction when unauthorized access remains plausible.
- Every recommendation and the top-level assessment required human approval.
- All structured policy citations resolved to passages supplied to the model.

### Manual grounding inspection

Evidence inspection:

- The unusual administrator login is directly supported by the input.
- The download of approximately 4,000 customer records is directly supported by the input.
- “MFA was reset for the administrator account” is a reasonable grammatical interpretation, but the input does not explicitly state whose MFA was reset. It should be treated as a small overstatement in an evidence field.

Action inspection:

- Preserving audit records is directly supported by `data-exfiltration#recommended-actions`.
- Recommending session revocation or temporary access restriction when active unauthorized access is plausible is directly supported by `authentication-security#recommended-actions`.
- Both actions were present in the actual model context and were correctly marked as requiring human approval.

### Problems discovered

- Confidence `0.9` is too high. The input does not confirm that the unusual location or MFA reset was unauthorized, that the download lacked business justification, or that data was transferred externally.
- The reasoning summary says that downloading 1,000 or more customer records constitutes high severity. The policy is narrower: it refers to an **unexplained export** of at least 1,000 records. Dropping “unexplained” overstates the rule.
- The `data_exfiltration` category is reasonable as a triage category, but the input establishes download rather than confirmed external disclosure. The current category vocabulary does not distinguish suspected from confirmed exfiltration.
- `account-compromise.md` is relevant to the combined unusual login and MFA reset but was outside the top-three section matches, demonstrating section-level TF-IDF's duplicate-source and vocabulary limitations.
- The action rationale names its supporting section in free text, but `RecommendedAction` does not yet carry a structured policy-reference field. Support was manually verifiable from the retained context but is not action-by-action machine-verifiable.
- Passing Pydantic and citation-membership checks did not prevent policy nuance from being misstated. This validates the need for the later reviewer stage and visible human inspection.

The manual test succeeded technically, but the above quality issues are intentionally retained in this record rather than treating schema validity as correctness.

## 2026-09-03 — Minimal Streamlit UI

### Files changed

- `app.py`: implemented the thin Streamlit presentation layer.
- `tests/test_app.py`: added Streamlit component tests for initial rendering and
  empty-input handling.
- `README.md`: added the local Streamlit launch command and current status.
- `planning/04_agent_journal.md`: recorded the UI implementation and smoke test.

### Interface decisions

- The page contains one incident text area and one `Analyze` button.
- The notice “Demonstration system using fictional policies. AI recommendations
  require human judgement.” is visible before and after analysis.
- `app.py` delegates the complete backend operation to `triage_and_review()`;
  it contains presentation and session-state handling, not retrieval, prompt,
  validation, or model orchestration logic.
- Results show category, severity, categorical confidence, concise summary,
  exact evidence, retrieved documents and TF-IDF scores, expandable cited policy
  text, policy-supported actions, reviewer checks, unsupported claims, warnings,
  and the human-approval requirement.
- Reviewer rejection is displayed as a separate error state while preserving the
  original assessment unchanged.
- Low confidence produces an explicit insufficient-evidence warning.
- Empty input, invalid/insufficient input, retrieval failure, Ollama
  unavailability, timeout, configuration problems, malformed or ungrounded model
  output, and unexpected local failures map to concise user-facing messages.
- No custom CSS, HTML rendering, policy upload, remediation control, or other UI
  infrastructure was added.

### Environment and dependency

- Streamlit was declared in `requirements.txt` but was not installed in the
  project virtual environment.
- Installed `streamlit==1.63.0` and its dependencies into `.venv`; no system-wide
  package installation was performed.

### Verification

- Full automated suite: **88 passed**.
- Streamlit started on the loopback-only address `127.0.0.1:8501`.
- `/_stcore/health` returned `ok`.
- A browser smoke test confirmed the title, explanation, fictional-policy notice,
  text area, Analyze button, progress indicator, all result sections, policy
  expanders, recommendation support, reviewer rejection state, reviewer warning,
  and human-approval notice.
- The end-to-end smoke test used the synthetic administrator/MFA/4,000-record
  incident with local `qwen3.5:9b`. The reviewer rejected the triage and the UI
  displayed that disagreement without replacing the assessment.
- The temporary Streamlit server was stopped after verification.
