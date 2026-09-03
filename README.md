# AI Incident Triage & Investigation Copilot

## Overview

A small, local-first demonstration application that converts an incident
narrative into a structured, policy-grounded triage proposal for human review.

> **Demonstration only:** the included policies are fictional and do not
> represent any real organization. Model output is advisory and requires human
> judgment.

The project demonstrates one bounded workflow:

> incident → retrieval → triage → deterministic validation → AI review → human decision

It is feature-complete as an MVP, not production-ready incident-response
software.

## Problem

Early incident reports are usually incomplete prose. An analyst must identify
the reported facts, find applicable guidance, estimate severity, determine what
remains unknown, and propose safe next steps. Doing this manually is slow and
inconsistent; doing it entirely with an LLM risks hallucination and false
confidence.

## What the application does

- Accepts one security or operational incident description.
- Retrieves up to three relevant local Markdown policy documents.
- Uses a local model to produce a Pydantic-validated `IncidentAssessment`.
- Deterministically checks evidence text, policy references, action support, and
  human-approval flags.
- Sends the unchanged assessment to a second, advisory reviewer call.
- Displays the assessment, retrieved sources, recommendations, reviewer
  concerns, and approval requirement in Streamlit.
- Fails visibly on invalid input, missing retrieval context, unavailable Ollama,
  timeout, malformed output, or fabricated structured references.

It never executes remediation.

## Architecture

```text
┌──────────────────┐
│ Streamlit UI     │
│ incident input   │
└────────┬─────────┘
         v
┌──────────────────┐     ┌─────────────────────────┐
│ Pydantic input   │────>│ TF-IDF retrieval        │
│ validation       │     │ five local .md files    │
└──────────────────┘     └───────────┬─────────────┘
                                     v
                         ┌─────────────────────────┐
                         │ Triage prompt + Ollama │
                         │ structured generation  │
                         └───────────┬─────────────┘
                                     v
                         ┌─────────────────────────┐
                         │ Pydantic + deterministic│
                         │ grounding validation   │
                         └───────────┬─────────────┘
                                     v
                         ┌─────────────────────────┐
                         │ Advisory reviewer call │
                         │ same local model       │
                         └───────────┬─────────────┘
                                     v
                         ┌─────────────────────────┐
                         │ Human decision         │
                         │ no execution path      │
                         └─────────────────────────┘
```

Core responsibilities stay outside Streamlit:

```text
app.py              presentation and safe failure states
src/retrieval.py    Markdown loading and deterministic TF-IDF ranking
src/schemas.py      input and model-output contracts
src/llm.py          replaceable interface and Ollama-specific adapter
src/triage.py       retrieval, triage, and grounding orchestration
src/reviewer.py     advisory review without rewriting the assessment
src/prompts.py      concise closed-context instructions
evals/              synthetic cases and real-pipeline evaluation runner
```

## Example workflow

For this input:

> An administrator account logged in from an unusual location, MFA was reset,
> and approximately 4,000 customer records were downloaded.

the application retrieves authentication, account-compromise, and
data-exfiltration guidance; proposes a category, severity, categorical
confidence, evidence, citations, and actions; validates the result; and shows a
separate reviewer judgment. The human decides whether the proposal is correct
and whether any recommended action should occur.

## Local-first design

Incident text, policies, retrieval, and inference remain on the machine. Ollama
hosts the model at `127.0.0.1:11434`, and the adapter rejects non-loopback model
hosts. Streamlit is checked in with `server.address = "127.0.0.1"` and the launch
command repeats that restriction.

Ollama was selected to avoid sending incident descriptions and fictional policy
context to a cloud model, to support offline experimentation, and to make the
model version explicit. Local execution reduces external disclosure; it does
not provide authentication, encrypted persistence, audit logging, or production
data governance. Use synthetic or sanitized incident text.

## Technology stack

- Python 3.12
- Streamlit
- Pydantic 2
- Ollama with `qwen3.5:9b`
- scikit-learn TF-IDF and cosine similarity
- Local Markdown policies
- pytest

`qwen3.5:9b` is a 9.7-billion-parameter Q4 model with an approximately 6.6 GB
download. It was selected as a practical quality/memory compromise for an
18 GB Apple Silicon machine. The application caps context at 8,192 tokens,
uses temperature zero, disables thinking output, and requests JSON matching the
Pydantic schema. The model can still be slow, incorrect, or inconsistent.

## Running locally

The following commands assume macOS, Homebrew, a fresh checkout in a directory
named `NCS`, and Python 3.12. Run them in order.

### 1. Enter the checkout and create the Python environment

```bash
cd NCS
python3.12 --version
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If `python3.12` is unavailable, install it with Homebrew, then repeat this step:

```bash
brew install python@3.12
```

### 2. Install or verify Ollama

```bash
if command -v ollama >/dev/null 2>&1; then
  ollama --version
else
  brew install ollama
fi
```

This project was verified with Ollama `0.33.2`. A newer compatible release may
also work but has not been evaluated here.

### 3. Start Ollama if required

For a Homebrew installation:

```bash
brew services start ollama
```

Verify that the local service responds:

```bash
ollama list
```

If `ollama list` reports that it cannot connect, wait a few seconds and retry.
For a non-service installation, run `ollama serve` in a separate terminal and
leave it running.

### 4. Install or verify the expected model

```bash
if ollama list | grep -q '^qwen3\.5:9b'; then
  echo "qwen3.5:9b is already installed"
else
  ollama pull qwen3.5:9b
fi
```

The pull downloads approximately 6.6 GB. It is intentionally explicit and is
never triggered by the application.

### 5. Configure this shell

```bash
export OLLAMA_HOST=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen3.5:9b
```

`.env.example` records these values for reference, but the application does not
automatically load `.env` files. Export the variables as shown. `OLLAMA_HOST`
already defaults to the loopback URL; `OLLAMA_MODEL` is required by the UI.

### 6. Start Streamlit

```bash
streamlit run app.py --server.address 127.0.0.1
```

Open [http://127.0.0.1:8501](http://127.0.0.1:8501) in the browser. Stop the
application with `Ctrl-C`.

Common startup issues:

- **First Streamlit launch asks for an email:** the prompt is optional; press
  `Enter` to continue.
- **No Ollama model configured:** export `OLLAMA_MODEL=qwen3.5:9b` in the same
  terminal used to start Streamlit.
- **Ollama unavailable:** run `brew services start ollama`, then check
  `ollama list`.
- **Model missing:** run `ollama pull qwen3.5:9b`.
- **Port 8501 already in use:** stop the other Streamlit process or add
  `--server.port 8502`, then open `http://127.0.0.1:8502`.
- **Slow first analysis:** the local model may need time to load into memory;
  each analysis makes both a triage and a reviewer request.

## Running tests

Tests do not require real model inference:

```bash
source .venv/bin/activate
python -m pytest
```

Current result: **90 passed**.

## Running evaluation

The evaluation invokes the actual local pipeline twice per case, so Ollama and
`qwen3.5:9b` must be available. From the repository root:

```bash
source .venv/bin/activate
export OLLAMA_HOST=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen3.5:9b
python evals/run_eval.py
```

The runner reports property-based outcomes rather than matching generated
wording. It does not rewrite expected values after observing results.

## Evaluation results

One recorded run on 12 synthetic cases using `qwen3.5:9b` produced:

| Metric | Result |
|---|---:|
| Structured triage and review outputs | 12/12 (100%) |
| Category accuracy | 12/12 (100%) |
| Severity accuracy | 12/12 (100%) |
| Required-policy retrieval hit rate | 12/12 (100%) |
| Human-approval compliance | 9/12 (75%) |
| Insufficient-information handling | 0/1 (0%) |
| Reviewer outcomes | 8 approved, 4 rejected |
| Cases with at least one failure reason | 7/12 |

The perfect category, severity, and retrieval scores are regression signals,
not evidence of real-world accuracy. The data is small, synthetic, close to the
policy vocabulary, and was evaluated once on one local model build. Of four
reviewer rejections, one caught a useful applicability error and three were
likely false positives.

See `planning/08_evaluation_results.md` for case-level analysis.

## AI safety and human oversight

- The model receives only the incident and retrieved policy context.
- Pydantic rejects unknown fields, invalid enums, malformed output, inconsistent
  approval state, and incomplete summaries.
- Evidence must occur in the incident text.
- Policy citations must resolve to sections supplied to the model.
- Recommendation text must occur in a cited policy section.
- Every generated action is structurally marked as requiring human approval.
- The reviewer reports disagreements separately and cannot rewrite triage.
- Provider and validation failures produce no fabricated fallback assessment.
- The application has no credentials, tools, remediation APIs, or action
  buttons. High-impact actions remain human-controlled because only an
  accountable person can assess context, authorization, and consequences that
  the model cannot establish.

The reviewer exists as a bounded second check for unsupported claims, policy
grounding, fabricated references, and approval mistakes. It uses the same local
model and is advisory—not independent assurance or a replacement for human
review.

## Key engineering decisions

- **TF-IDF over keyword matching:** still simple and deterministic, but ranks
  multi-term relevance more credibly than hand-written keyword counts.
- **No embeddings or vector database:** five short policies fit comfortably in
  memory, lexical retrieval is transparent, and vector infrastructure would add
  dependencies and opacity without solving policy applicability.
- **Document-level retrieval:** prevents several sections from one policy from
  crowding out another relevant document; all sections of selected documents
  remain traceable.
- **Pydantic at trust boundaries:** structured generation is not trusted until
  application validation succeeds.
- **Application-owned source resolution:** the model returns identifiers; Python
  resolves the authoritative policy text.
- **No automatic repair loop:** malformed or ungrounded results fail clearly
  instead of being silently transformed by another model call.
- **Categorical confidence:** `low`, `medium`, or `high` avoids unsupported
  decimal precision.
- **Capability removal:** preventing execution is a stronger MVP control than
  asking a model not to remediate.

## Trade-offs

- Exact-substring evidence and action checks are clear and testable but do not
  understand semantic applicability.
- TF-IDF is sufficient for the curated corpus but weak on synonyms,
  out-of-domain incidents, and changing vocabulary.
- Supplying complete selected documents improves guidance coverage but includes
  irrelevant text.
- Local inference improves privacy and control but adds model installation,
  memory use, latency, and machine-specific variability.
- A same-model reviewer can catch mistakes but shares blind spots and generates
  false positives.
- The synchronous, in-memory design is easy to understand but is not a durable,
  multi-user case system.

## How Codex was used during development

Codex helped define and challenge the product scope, inspect the Mac development
environment, create the fictional corpus, implement each layer incrementally,
write deterministic tests, exercise real local inference, inspect results
against their sources, build the evaluation harness, perform a security review,
and simplify the finished code. Significant steps and observed failures are
recorded in `planning/04_agent_journal.md` and `planning/12_retrospective.md`.

## Examples where Codex needed correction

Successful generation did not mean correct behavior. During real-model testing:

- Evidence changed “MFA was reset” into “MFA was reset for the administrator
  account,” adding an unsupported relationship. Exact incident-text validation
  was added.
- Confidence `0.9` implied calibration the project did not have. Confidence was
  changed to categorical values.
- Asking the model to quote policy caused it to combine separate bullets and add
  ellipses. Quotation was removed; Python now resolves exact source text.
- A generated action set `human_approval_required` to `false` despite prompt
  instructions. The action field was constrained to literal `true`.
- The evaluation recommended preserving an alert when the incident explicitly
  said no alert existed. This remains a documented semantic-applicability
  limitation; the reviewer caught that case.

## Limitations

- A copied, correctly cited policy action may still be inapplicable to the facts.
- Incident and policy prompt injection is mitigated mainly by instructions and
  capability removal, not eliminated.
- Local policy files are trusted; there is no manifest, signature, lifecycle,
  freshness, or conflict management.
- Retrieval can return a weak lexical match and has limited adversarial or
  out-of-domain coverage.
- Confidence is not calibrated.
- The same-model reviewer is inconsistent and not independent verification.
- The dataset is too small and synthetic to establish production quality.
- Incident text lives in process memory during use; there is no formal retention
  or sensitive-data control system.
- Human approval is displayed as a requirement but is not durably recorded.

## What I deliberately did not build

- Autonomous remediation or operational security integrations
- A complete SOC, SIEM, SOAR, EDR, IAM, or case-management workflow
- Cloud infrastructure, Kubernetes, a production database, or a vector database
- Authentication, roles, multi-user collaboration, or persistent incidents
- Policy upload, editing, synchronization, or governance
- An agent framework, background workers, repair loops, or tool use
- Legal, regulatory, breach-notification, or forensic conclusions
- Model fine-tuning or training infrastructure

## Production evolution / next steps

Before any operational use, the next priority is explicit recommendation
applicability: preserve each policy precondition and show whether it is known or
unknown. Add structured insufficient-information signals, weak-match and
out-of-domain retrieval tests, prompt-injection cases, controlled policy
publishing, and reviewer false-positive measurement.

A production system would additionally need authentication and authorization,
encrypted persistence, retention rules, audit trails, model/prompt versioning,
policy ownership and integrity controls, representative evaluations, monitoring,
and a separately designed approval workflow. Embeddings or hybrid retrieval
should be considered only if measured corpus growth or lexical misses justify
them—not merely because the application uses retrieval-augmented generation.
