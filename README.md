# AI Incident Triage & Investigation Copilot

A small, local-first decision-support application for turning an incident narrative into a policy-grounded triage brief for human review.

The intended workflow is:

> Incident → retrieval → triage → verification → human decision

The application will recommend investigation or containment actions but will not perform remediation. Every recommendation remains subject to an explicit human decision.

## Status

The repository currently contains planning documents, the fictional policy corpus, and a tested TF-IDF policy retrieval layer. Prompts, Ollama inference, structured triage, review, evaluation, and the Streamlit workflow have not been implemented yet.

## Intended stack

- Python 3.12
- Streamlit
- Pydantic
- Ollama with a deliberately selected local model
- Local Markdown policies
- scikit-learn TF-IDF retrieval
- pytest

## Prerequisites

- Python 3.12 or another compatible modern Python version.
- Ollama installed and listening only on a local interface.
- A local Ollama model selected with regard to memory use and structured-output quality.

No Ollama model is selected by this scaffold. Model installation should be an explicit decision because model downloads can be large.

## Local setup

After Ollama and a model have been selected:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Set `OLLAMA_MODEL` in `.env`. Until configuration loading and the application pipeline are implemented, the scaffold is not expected to run end to end.

## Repository layout

```text
.
├── app.py                 # future Streamlit entry point
├── src/                   # core schemas and pipeline stages
├── data/policies/         # local Markdown knowledge base
├── evals/                 # synthetic cases and evaluation entry point
├── tests/                 # deterministic tests
└── planning/              # product and architecture decisions
```

## Safety boundary

The model will have no operational tools, credentials, or remediation integrations. Structured output, citation membership, and human-decision requirements will be enforced by deterministic code before a result is treated as valid.
