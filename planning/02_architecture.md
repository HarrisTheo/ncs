# Technical Architecture

## Goal and constraints

Build a small, local-first decision-support application that turns one incident narrative into a policy-grounded triage brief, verifies it, and presents it to a human for a final decision.

The fixed flow is:

> Incident → retrieval → triage → verification → human decision

For this MVP, **verification** has two parts: deterministic checks followed by an advisory LLM review. “Agent” means one bounded Ollama request with a Pydantic output schema. There is no agent framework, tool use, memory, planning loop, background work, or autonomous action.

The implementation should be achievable in a few hours. The initial knowledge base contains approximately five small Markdown documents.

## Architecture diagram

```text
                             LOCAL MACHINE

  untrusted text                                              human authority
       |                                                             ^
       v                                                             |
+--------------+    +--------------+    +----------------+    +------+-------+
| Streamlit UI |--->| Input checks |--->| Policy search  |    | Human review |
| one incident |    | Pydantic     |    | Markdown       |    | and decision |
+--------------+    +--------------+    | TF-IDF/cosine  |    +------+-------+
                                               |                    ^
                           policies/*.md ------+                    |
                                               v                    |
                                      +--------+---------+          |
                                      | Triage LLM call  |          |
                                      | Ollama + schema  |          |
                                      +--------+---------+          |
                                               |                    |
                                               v                    |
                                      +------------------+          |
                                      | Deterministic    |          |
                                      | verification     |          |
                                      | schema, sources, |          |
                                      | approval invariant|         |
                                      +--------+---------+          |
                                               |                    |
                                               v                    |
                                      +------------------+          |
                                      | Reviewer LLM call|----------+
                                      | advisory findings|
                                      +------------------+

  pytest + synthetic fixtures exercise the pure functions and selected
  end-to-end model behavior; they are not a separate runtime service.
```

## Design principles

1. **Local by default.** The incident, policies, prompts, and inference remain on the machine.
2. **The model proposes; code constrains; the human decides.** No model output is authorization.
3. **Visible grounding.** The UI shows every retrieved passage and resolves citations to it.
4. **Facts are not hypotheses.** Observations, inferences, and unknowns are separate fields.
5. **Explicit failure.** The application does not hide invalid output or missing evidence.
6. **Few moving parts.** One Python process, one local Ollama endpoint, no persistence service, and no agent framework.

## Component responsibilities

### Streamlit UI

- Collect one required natural-language incident description.
- Warn against entering secrets or unnecessary personal data.
- Run the synchronous pipeline and show simple stage progress.
- Display retrieved evidence, triage, verification outcomes, and reviewer findings as separate sections.
- Let the human accept or override severity and approve, reject, or defer every recommendation.
- Provide a JSON download of the completed brief.

Streamlit session state holds only the current working result. Refreshing or stopping the process may lose it. There is no case database, authentication, collaboration, or server API.

### Input validation

- Require non-empty text.
- Apply a conservative maximum length and normalize ordinary whitespace.
- Represent the accepted input with a small Pydantic model.

The UI accepts no policy upload, arbitrary path, rich HTML, or operational credentials.

### Policy retrieval

- Read `.md` files from one fixed project policy directory.
- Split each document by headings.
- Generate passage identifiers deterministically from the file name and heading, adding a suffix for duplicate headings.
- Build an in-memory TF-IDF matrix and rank passages with cosine similarity.
- Return the top three passages with identifier, title, heading, text, and score.
- Stop with a visible error if the corpus cannot be loaded or every similarity score is zero.

The index is rebuilt on application startup or Streamlit cache invalidation. There is no file watcher, persisted index, custom indexing job, score-tuning UI, or retrieval service.

Policy metadata should use a tiny documented convention that can be parsed without a Markdown or YAML library. Only metadata that appears in the UI or export should be required.

### Triage LLM call

- Receive the validated incident, the top retrieved passages, concise instructions, and the Pydantic-generated JSON schema.
- Return observed facts, inferences, unknowns, category, possible impact, proposed severity, confidence, citations, investigation questions, recommendations, and limitations.
- Use only passage identifiers present in the prompt.

This is one Ollama call. It has no tools and cannot load files or execute actions. Prompt text and the request function live together in one small module; there is no provider abstraction or triage-agent class hierarchy.

### Deterministic verification

- Parse the response with Pydantic.
- Enforce enumerations, required fields, bounds, and basic cross-field invariants.
- Reject citations that do not resolve to one of the retrieved passages.
- Require rationale and a citation for policy-based recommendations.
- Require a human disposition for every recommendation, regardless of its apparent impact.
- Return a short list of blocking errors and non-blocking warnings.

The verifier does not decide incident facts, infer category, or compute severity. It does not implement a general rule engine or duplicate the policy documents in code. If a later policy contains an unambiguous safety invariant, it may be added as one explicit tested function.

There is no automatic model repair loop. Invalid model output is shown as a failed triage with concise validation errors; the user may retry the complete triage request. This is simpler and avoids a second, difficult-to-explain transformation of the model's answer.

### Reviewer LLM call

- Run only after the triage result passes deterministic verification.
- Receive the original incident, the same passages, and the validated triage result.
- Return a small structured list of findings: unsupported claim, missed evidence, excessive certainty, citation concern, severity concern, or unsafe recommendation.
- Never rewrite the triage result or set the human decision.

The reviewer is a second prompt through the same Ollama request function, not a second autonomous subsystem. Because the same model may repeat its own mistake, the review is labelled advisory. If it fails, the UI shows “review unavailable” and still allows the human to inspect the validated triage. Evaluation should determine whether this pass adds enough value to retain.

### Human decision

- Preserve the model proposal and reviewer findings rather than silently merging them.
- Capture the human's final severity and optional override note.
- Capture approve, reject, or defer for each recommendation.
- Generate a JSON download containing the incident, evidence, triage, verification, review status, and human decision.

All recommendations require an explicit human disposition. “Approved” means recorded as approved in the brief; the application still performs no action.

### Evaluation harness

- Use ordinary pytest tests and a small set of version-controlled synthetic fixtures.
- Test document parsing, deterministic passage identifiers, retrieval ranking, Pydantic validation, citation membership, and the approval invariant without Ollama.
- Keep Ollama-dependent evaluations behind an explicit pytest marker.
- Assert properties such as critical-fact coverage, retrieved source, valid citations, and safe recommendation handling rather than exact prose.
- Record the tested model name and prompt version in model-evaluation output.

There is no evaluation framework, dashboard, experiment database, or separate command-line application in the MVP.

## Minimal data contracts

Use Pydantic only at trust boundaries or where structured model output requires it:

- `IncidentInput`: the validated description.
- `PolicyPassage`: identifier, source, heading, text, and retrieval score.
- `TriageResult`: the complete structured triage, including nested recommendations.
- `ReviewResult`: advisory findings and an optional summary.
- `HumanDecision`: final severity, recommendation dispositions, and notes.

Verification errors can be ordinary typed Python values; they do not require an extensible result hierarchy. The downloadable brief can be assembled from the validated models rather than introducing another domain abstraction.

## Data flow

1. The user submits an incident description.
2. Pydantic rejects empty or oversized input before inference.
3. The retriever loads and chunks the fixed Markdown corpus, builds TF-IDF vectors, and returns the top three passages.
4. The UI retains and displays exactly those passages.
5. One Ollama call produces the proposed `TriageResult`.
6. Pydantic and deterministic verification accept it or stop with visible errors. There is no automatic repair call.
7. A valid result is sent through the same Ollama client for the structured reviewer pass.
8. The UI presents the incident, passages, triage, verifier outcome, and either reviewer findings or an explicit “unavailable” state.
9. The human records the final decision and may download one JSON brief.

The pipeline is sequential and synchronous. Async execution, queues, jobs, callbacks, and streaming model output are unnecessary.

## Retrieval comparison and decision

| Approach | Advantages | Costs and weaknesses | MVP fit |
|---|---|---|---|
| Keyword search | Almost no code or dependencies; maximally transparent | Weak ranking; brittle when incident and policy vocabulary differ | Useful baseline, but fragile as the only method |
| TF-IDF + cosine similarity | Deterministic, local, fast, ranked, testable, and easy to inspect | Does not capture semantic equivalence; adds scikit-learn | Best small compromise |
| Embeddings + vector search | Better semantic matching across different wording | Adds an embedding model, index lifecycle, versioning, latency, and harder evaluation | Unnecessary for five small documents |

Use **TF-IDF with cosine similarity** in process through scikit-learn. For five documents, the dependency is a larger cost than the computation, but it avoids writing a custom ranker and gives a more credible retrieval demonstration than exact keyword counts. No embeddings or vector database are used.

The top-k value is fixed at three for the MVP. A zero-score result is treated as ungrounded rather than tuned through an arbitrary relevance threshold. Retrieval tests, not architectural speculation, decide whether TF-IDF is adequate.

## Minimal project structure

```text
NCS/
├── planning/
├── policies/                       # approximately five Markdown files
├── evaluations/
│   └── cases.json                  # a few synthetic cases
├── src/
│   └── incident_copilot/
│       ├── app.py                  # Streamlit UI
│       ├── models.py               # Pydantic contracts
│       ├── retrieval.py            # load, chunk, and rank policies
│       ├── llm.py                  # prompts plus both Ollama calls
│       ├── verification.py         # small deterministic checks
│       └── pipeline.py             # sequential orchestration
├── tests/
│   ├── test_retrieval.py
│   ├── test_verification.py
│   └── test_pipeline.py
├── pyproject.toml
└── README.md
```

This is a maximum initial structure, not a requirement to create empty files. Export assembly stays in the UI or pipeline until it becomes complex enough to justify a module. Prompts stay in `llm.py`; configuration is a few constants or environment variables, not a framework.

## Trust boundaries

### User and document text

Incident text is untrusted and policy text may be stale, malformed, or compromised. Both are delimited as data in prompts. This reduces prompt-injection risk but cannot guarantee that a model will ignore malicious text. The strongest mitigation is that the model has no tools, credentials, or execution path and its citations and structure are checked.

### Ollama and model output

Ollama is a separate local process and the model is an untrusted reasoning component. Local inference improves privacy, not correctness. Model output must pass Pydantic and deterministic checks before being displayed as valid.

### Application rules

The fixed policy directory, accepted schemas, citation membership, and human-disposition invariant are trusted application controls. They must be short, explicit, and covered by tests.

### Human authority

Only the human records the final decision. No UI event or model field maps to an operational API.

### Download boundary

The JSON brief can contain sensitive information. Download is explicit, and the user controls its storage. The MVP does not silently write, synchronize, encrypt, or retain incident files.

## Important failure modes

| Failure | MVP behavior |
|---|---|
| Ollama unavailable or model missing | Stop inference and show the local configuration problem |
| Empty or oversized incident | Reject before retrieval |
| Missing, unreadable, or malformed policy corpus | Stop and name the affected file |
| All retrieval scores are zero | Stop or clearly label the run ungrounded; do not call the triage grounded |
| Relevant passage is ranked outside the top three | Expose results and catch representative misses in retrieval tests |
| Triage output is malformed | Show validation errors; do not automatically repair or continue |
| Citation is invented | Reject the triage result |
| A plausible claim is unsupported | Rely on visible evidence, reviewer findings, and human judgment; schema validity is not truth |
| Recommendation omits human review | Reject it; every recommendation requires a human disposition |
| Reviewer disagrees | Show both results without merging |
| Reviewer fails | Label review unavailable and allow human inspection of the already validated triage |
| Policy documents conflict | Show their source text; do not let the model silently establish precedence |
| Streamlit refreshes or exits | Current work may be lost unless the user downloaded it |

## Security considerations

- Bind Streamlit and Ollama to loopback interfaces for the MVP; do not expose them to the local network or internet.
- Use a fixed, resolved policy directory and do not accept paths from the user.
- Treat Markdown, incident content, and model output as text; do not enable unsafe HTML or execute generated content.
- Bound incident length, retrieved context, model output tokens, request timeout, and retry count.
- Do not log incident text, prompts, policy passages, model responses, or downloaded briefs by default.
- Do not give the model credentials, shell access, tools, plugins, or operational API clients.
- Validate citation identifiers against the actual retrieved set, not the whole corpus.
- Require a human disposition for every recommendation and make clear that disposition has no operational effect.
- Use synthetic or sanitized incidents in tests.
- Treat local-first as reduced exposure, not a guarantee: the host, Ollama process, local files, browser downloads, and backups remain in scope for the user.

## Technology choices

- **Python:** one runtime with strong support for the selected tools and simple pure-function testing.
- **Streamlit:** the quickest credible local review UI; business logic remains in importable functions.
- **Pydantic:** validates user input and structured LLM boundaries and can supply the requested JSON schema.
- **Ollama:** provides local inference on the target Mac without sending incident data to a hosted model.
- **Markdown:** keeps the five-document corpus readable, editable, and version-controlled.
- **scikit-learn:** supplies tested TF-IDF and cosine ranking without a retrieval service or custom algorithm.
- **pytest:** covers deterministic behavior and marked model evaluations without an additional harness.

Expected direct application dependencies are limited to Streamlit, Pydantic, scikit-learn, and a small Ollama client. A standard-library HTTP call may replace the client if that proves clearer during implementation; there is no multi-provider abstraction.

## What changes at production scale

Production changes are deferred until evidence justifies them:

- A larger, permissioned corpus needs document governance, versioning, access filtering, and a retrieval benchmark. Embeddings or a persisted index should be added only after measured TF-IDF failures.
- Multiple users need authentication, role separation, encrypted durable storage, concurrency control, retention, deletion, and tamper-evident audit records.
- Higher assurance needs independent security review, larger adversarial evaluations, model and prompt release gates, and possibly a genuinely independent reviewer model.
- Concurrent use may require an API boundary, job management, model-serving separation, cancellation, rate limits, and redacted observability.
- Read-only evidence integrations need narrow service identities and data minimization.
- Any remediation capability would be a separately designed system with explicit authorization and audit controls, not an extension of the MVP's approval widgets.

The production system should preserve the same central boundary: retrieval supplies visible evidence, the model proposes a structured assessment, deterministic code enforces invariants, and a human owns consequential decisions.

## Final decision

Implement one synchronous local Python application with six small source modules, an in-memory TF-IDF retriever over approximately five Markdown policies, one structured Ollama triage call, one advisory reviewer call, deterministic Pydantic and citation checks, a Streamlit decision screen, a JSON download, and ordinary pytest tests.

Do not add a database, vector store, web API, orchestration framework, rule engine, repair loop, background worker, model-provider framework, or remediation integration.
