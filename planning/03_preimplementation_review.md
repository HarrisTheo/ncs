# Pre-implementation Architecture Review

## Review stance

This review assumes the goal is to demonstrate the core product pattern within a few hours, not to create a foundation for an imagined production platform. The relevant question is not whether each proposed component could eventually be useful; it is whether it improves the credibility of this MVP enough to justify its implementation and testing cost now.

## Verdict

The original architecture had sensible safety boundaries and technology choices, but its proposed module layout, validation behavior, configuration surface, and artifact model were drifting toward a small platform. The core demonstration needs only:

> one incident → three retrieved passages → one structured triage → deterministic checks → one advisory review → one human decision

The architecture has been simplified accordingly. The reviewer remains because it is part of the stated product hypothesis, but it is explicitly one second LLM request—not an autonomous agent—and its value must be demonstrated rather than assumed.

## What I challenged

### Too many modules for the amount of behavior

The original structure proposed separate modules for configuration, policy parsing, retrieval, Ollama access, prompts, triage, review, pipeline orchestration, and export. That would create many boundaries around very small functions and make navigation slower without providing meaningful isolation.

For a few-hour project, the better testability boundary is between the Streamlit UI and pure Python functions. Six compact source modules are enough. Policy parsing belongs with retrieval; both prompts belong with the Ollama request code; JSON export does not need its own service.

### “Agent” language implied more capability than exists

Calling triage and review “agents” can encourage agent frameworks, classes, tool interfaces, memory, retries, and orchestration. None improves this product. Both stages are bounded structured model requests. They share one small Ollama function and have no tools or autonomy.

### The reviewer could be unnecessary AI

A second call to the same model is not independent validation and may reproduce the first call's error. It adds latency, nondeterminism, another schema, and more UI state.

I recommend keeping it only as a narrowly scoped advisory critique because the original product concept explicitly includes AI review and because implementing a second prompt through the same client is small. It must not block human access to a valid triage if it fails. Model evaluation should measure whether it catches seeded omissions or unsupported claims; if it does not, remove it.

### Automatic model repair adds opaque behavior

The original design allowed a repair call after schema failure. This complicates traces and tests, can change substantive content while appearing to fix formatting, and introduces another failure path. It is unnecessary for a local MVP.

The revised design fails visibly on invalid triage output and lets the user rerun the complete request. Zero automatic repairs satisfies the existing constraint of no more than one repair attempt.

### A deterministic severity engine would duplicate policy and create false assurance

The architecture referred to minimum-severity and consistency rules without first defining a small, authoritative rule set. Encoding policy both in Markdown and code risks divergence. Worse, deterministic-looking severity can appear more trustworthy even when it depends on facts extracted by the model.

The revised verifier checks structure, citation membership, and human-decision invariants. It does not calculate severity. Expected severity is tested in synthetic model evaluations. A direct deterministic rule should be added only when a policy states an unambiguous invariant that can be expressed and tested without reimplementing incident judgment.

### Impact classification made approval logic harder than necessary

The previous design distinguished high-impact actions and proposed logic to ensure only those require approval. This requires a complete and reliable action taxonomy. A recommendation can be phrased in unexpected ways, so classification itself becomes a safety weakness.

For the MVP, every recommendation requires a human approve, reject, or defer decision. This is both simpler and safer. Approval remains only a recorded disposition and never triggers an action.

### Too many domain models

The original design listed separate document, verification, recommendation, brief, and other contracts. Pydantic is valuable at untrusted boundaries, but creating a model for every internal value adds ceremony.

The revised design keeps five main Pydantic contracts: incident input, policy passage, triage result, review result, and human decision. Nested recommendations remain part of the triage result. Internal verification errors can be ordinary typed Python values, and the downloadable JSON can be assembled from validated models.

### Policy metadata and indexing lifecycle were too ambitious

With five documents, an index cache, file watcher, persisted index, metadata framework, or general Markdown parser is unnecessary. Stable citations do matter, but explicit identifiers in every section are not required.

The retriever now loads a fixed directory, splits on headings, generates identifiers from file names and headings, and builds TF-IDF in memory. Metadata uses a tiny documented convention parsed without another dependency.

### The retrieval threshold could become tuning theater

Cosine scores from a five-document TF-IDF corpus are corpus-relative. A configurable “minimum relevance” threshold would look rigorous while being poorly calibrated.

The MVP uses a fixed top three. If every score is zero, grounding has clearly failed. Other retrieval quality is assessed with examples rather than a speculative threshold control.

### Dual export formats did not improve the demonstration

Supporting JSON and Markdown immediately doubles formatting and snapshot-test work. JSON already preserves structure and can be inspected or transformed later.

The revised MVP offers only a JSON download. It does not implement arbitrary filesystem writes or persistent case storage.

### Configuration was becoming a subsystem

A configuration module with validated model, endpoint, limits, top-k, prompt versions, and rule versions is more machinery than this MVP needs. Most values can be safe constants. Only the Ollama model or endpoint may reasonably vary through a documented environment variable.

No general settings UI or configuration framework should be built.

### The evaluation harness sounded like a separate product

The original evaluation responsibilities included result recording and summaries that could lead to a custom runner or experiment store. For the MVP, the harness is pytest plus a few JSON fixtures and one marker for Ollama-dependent cases.

Deterministic tests run normally. Model evaluations record enough identifying information in test output to reproduce a run, but there is no dashboard or database.

## Security weaknesses identified

### Prompt delimiters are not a security boundary

Clearly labelling incident and policy text as data helps but cannot guarantee prompt-injection resistance. The meaningful protection is removal of capability: neither model call has tools, credentials, arbitrary file access, shell access, network integrations, or remediation functions. Citation membership and Pydantic validation further limit how output is accepted.

### “Local” could still mean network-accessible

Streamlit and Ollama can be bound beyond loopback. The MVP must use loopback-only defaults and must not be represented as safe for shared or exposed deployment. There is no authentication.

### Rendering and file selection could enlarge the attack surface

Unsafe HTML rendering, user-selected policy paths, or Markdown execution would be unnecessary risks. The UI should render content as text, and retrieval should use a fixed resolved project directory containing `.md` files only.

### Logging and downloads can leak incident data

Local inference does not protect terminal logs, debug output, browser downloads, backups, or screen capture. Raw inputs and prompts should not be logged by default. JSON download must be explicit and labelled as potentially sensitive.

### Approval wording could mislead users

An “Approve” button may appear to perform containment. The UI and exported schema must say that it records a recommendation disposition only. There is no operational client anywhere in the process.

### Resource exhaustion remains possible locally

Very large input, context, or output can stall local inference. Fixed input length, top-three retrieval, bounded generation, timeout, and no automatic retry keep this risk understandable.

## Difficult-to-test areas

### Model correctness

Pydantic can prove shape, not factual quality. Tests should not compare exact prose. A few synthetic cases should assert necessary properties: required facts are represented, citations are valid, expected policies are retrieved, recommendations require human disposition, and severity is not below a scenario-specific expectation.

### Reviewer value

It is easy to test that the reviewer returns valid JSON but harder to show it improves safety. Include a small number of deliberately flawed triage fixtures and verify that the reviewer identifies the seeded issue often enough to be useful. Treat this as evidence, not a deterministic unit test.

### Streamlit behavior

Heavy UI automation would consume the project's time budget. Keep decisions and pipeline steps in pure functions, manually smoke-test the short UI path, and focus pytest on retrieval and verification. Do not build a page-object test suite.

### Model availability and versions

Normal tests must not require Ollama. Mark model tests explicitly and report the model name. Model-dependent failures should not be confused with deterministic regressions.

## What I recommend simplifying

- Use six small source modules at most; merge further if files remain trivial.
- Use one incident text area rather than a configurable intake form.
- Generate citations from filenames and headings.
- Retrieve a fixed top three with in-memory TF-IDF.
- Use one shared Ollama request function and two prompt functions.
- Remove automatic repair calls.
- Remove a general severity or policy rule engine.
- Require human disposition for every recommendation.
- Offer JSON download only.
- Use constants and at most a couple of environment variables instead of a configuration system.
- Use pytest fixtures and markers instead of a separate evaluation application.
- Use Streamlit session state only; do not add persistence.

## What I recommend keeping

### TF-IDF retrieval

Keyword counts would be marginally smaller, but TF-IDF ranking is a more credible demonstration and scikit-learn avoids custom ranking code. Embeddings and a vector database remain unjustified for five documents.

### Pydantic at trust boundaries

Structured outputs are central to the product, and local models can be inconsistent. Pydantic provides real value for incident input, both model responses, citations, and human decisions.

### Visible retrieved passages and citation checking

This is the main grounding mechanism and lets the human discover retrieval failure. Removing it would undermine the product hypothesis.

### Separation of facts, inferences, and unknowns

This is a high-value safety and usability constraint with little implementation cost.

### The bounded reviewer pass

Keep it as an explicit experiment because it is part of the proposed workflow and is cheap to add through the same model client. Label it advisory, let failures degrade gracefully, and remove it later if evaluation shows no useful improvement.

### Human recommendation dispositions

The human decision is not decorative; it demonstrates the safety boundary. Every recommendation must receive an explicit approve, reject, or defer value before a completed brief is downloaded.

### Local-only execution and no persistence

These choices reduce data exposure and implementation time. They are appropriate for a single-user demonstration, with clear warnings that local execution is not equivalent to production security.

## Changes made to `02_architecture.md`

The architecture document was revised to:

- Reduce the proposed source layout from twelve modules to at most six.
- Define both “agents” as two bounded calls through one Ollama module.
- Remove automatic structured-output repair.
- Remove the proposed general minimum-severity and policy rule mechanism.
- Require a human disposition for every recommendation rather than classifying only some actions as high impact.
- Reduce the conceptual Pydantic model set.
- Merge policy loading with retrieval and prompts with LLM access.
- Replace configurable retrieval thresholds with fixed top-three retrieval and a zero-score failure.
- Replace JSON-or-Markdown export with a single JSON download.
- Make reviewer failure non-blocking and visibly labelled.
- Remove separate runtime evaluation, export, configuration, provider, indexing, and background-work abstractions.
- Strengthen loopback-only, fixed-path, safe-rendering, bounded-resource, and no-sensitive-logging guidance.

## Implementation gate

The revised architecture is small enough to implement in a few hours if the first pass remains disciplined:

1. Five short policies and a heading-based retriever.
2. One Pydantic triage schema and one concise prompt.
3. Citation and human-disposition checks.
4. One small reviewer schema and prompt.
5. One Streamlit page.
6. A few deterministic tests and two or three synthetic model evaluations.

Anything beyond that list should be treated as optional until the end-to-end path works and has been evaluated.
