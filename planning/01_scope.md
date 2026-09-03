# MVP Scope

## Scope statement

The MVP is a local, single-user application that turns one natural-language incident description into a policy-grounded, structured triage brief that is verified before a human records the final decision.

Its complete workflow is:

> Incident → retrieval → triage → verification → human decision

The MVP ends at a recorded recommendation and human decision. It does not perform remediation or attempt to reproduce the functions of a complete Security Operations Center.

## MVP features

### 1. Incident input

- A Streamlit form for a natural-language incident description.
- A small number of optional context fields, such as affected system, time, account, or data type.
- Guidance warning users not to enter secrets or unnecessary personal data.
- One active incident at a time.

### 2. Local policy and playbook corpus

- Policies and playbooks stored as local Markdown files.
- Simple required metadata: document title, version, owner, review date, and stable section identifiers.
- A small curated starter corpus covering incident classification, severity, account compromise, suspected data exfiltration, evidence handling, and approval requirements.
- Read-only use of policy content by the application.

### 3. Lightweight retrieval

- Markdown content split primarily by headings into identifiable passages.
- A transparent local lexical search method, such as BM25 or TF-IDF.
- A small configurable limit on retrieved passages.
- Display of the retrieved passage text, document source, and section identifier.
- No external retrieval service or vector database.

### 4. Structured AI triage

- Local inference through Ollama.
- A Pydantic-defined triage result containing:
  - Incident category.
  - Observed facts.
  - Inferences or hypotheses.
  - Unknowns and investigation questions.
  - Potentially affected assets or data.
  - Proposed severity and confidence.
  - Policy citations and rationale.
  - Recommended investigation or containment actions.
  - Human-approval requirement for every recommendation.
  - Limitations or cautions.
- Clear separation between facts, inferences, and unknowns.

### 5. Deterministic verification

- Pydantic parsing and schema validation.
- Validation of allowed categories, severity values, confidence bounds, and action types.
- Verification that cited passage identifiers were included in the retrieved context.
- Enforcement that high-impact actions are marked as requiring human approval.
- A small, documented set of deterministic safety and minimum-severity rules.
- At most one structured retry when model output is invalid, followed by a visible failure if validation still does not succeed.
- No silent repair of substantive model claims or decisions.

### 6. AI review

- A second structured model pass over the incident, retrieved passages, and validated triage draft.
- Findings limited to unsupported claims, missing considerations, citation problems, excessive certainty, severity inconsistencies, and unsafe recommendations.
- Review findings shown separately from the original triage result.
- The reviewer may challenge the draft but cannot authorize actions or overwrite the human decision.

### 7. Human decision

- A review screen showing the original incident, retrieved evidence, triage result, deterministic verification, and AI review findings.
- Controls to accept or override the proposed severity.
- Controls to approve, reject, or defer each recommendation.
- A field for human decision notes.
- Optional local export as JSON and/or Markdown.
- No connection from an approval control to an operational system.

### 8. Tests and evaluation

- `pytest` tests for document parsing, retrieval behavior, schemas, citation validation, approval rules, and core pipeline behavior.
- A small version-controlled set of synthetic incident scenarios.
- Evaluation assertions based on required properties rather than exact wording, including relevant source retrieval, critical-fact coverage, minimum severity, approval flags, and absence of unsupported claims.
- Tests that can run without invoking Ollama wherever model inference is not specifically under evaluation.

## Acceptance criteria

The MVP is acceptable when all of the following are true:

1. A user can submit one incident narrative in the local Streamlit application and receive either a complete triage result or a clear, recoverable error.
2. The application retrieves passages only from the configured local Markdown corpus and shows those passages to the user.
3. The triage output conforms to the defined Pydantic schema before it is displayed as valid.
4. Every policy citation in a valid triage output resolves to a passage actually supplied to the model.
5. Reported facts, model inferences, and unknowns appear in separate fields.
6. Every recommendation includes rationale and an explicit approval requirement.
7. High-impact actions, including account suspension, session revocation, system isolation, data deletion, or access removal, can never be presented as automatically executable or pre-authorized.
8. Invalid model output receives no more than one repair attempt and never bypasses validation.
9. The AI reviewer returns structured findings and cannot silently replace the validated triage result.
10. The user can accept or override severity and approve, reject, or defer each recommendation before exporting a final brief.
11. No UI control, model output, or export operation performs remediation or calls an operational security system.
12. Automated tests cover the deterministic safety boundaries and pass locally.
13. The evaluation set contains representative synthetic cases for at least account compromise and suspected data exfiltration.
14. The application and its core workflow can be understood and run locally without cloud infrastructure, a production database, or an external vector database.

## Explicit non-goals

- Replacing an incident responder, incident commander, or final decision-maker.
- Simulating a complete Security Operations Center.
- Detecting incidents from live telemetry.
- Performing digital forensics or declaring root cause.
- Executing containment, remediation, recovery, or notification actions.
- Guaranteeing that the model's assessment is correct or complete.
- Providing legal, regulatory, or compliance determinations.
- Managing the entire incident lifecycle.
- Supporting multiple organizations, tenants, or policy domains.

## Assumptions

- The application runs locally on a MacBook M3 Pro.
- Python is the primary implementation language and Streamlit is the UI framework.
- Ollama is installed separately and a suitable local model is available.
- The selected model is capable of following concise structured-output instructions, although failures are expected and handled.
- The policy corpus is small, curated, internally consistent enough for an MVP, and stored as Markdown.
- Policy owners are responsible for document accuracy, versioning, and review dates.
- Users understand basic incident-response concepts and remain accountable for decisions.
- MVP incidents are manually entered and small enough to fit comfortably within the selected model's context window.
- Synthetic or sanitized incident data can be used for development and evaluation.
- Single-process, single-user execution is sufficient.

## Major risks

### Retrieval misses the relevant guidance

Lexical retrieval may not find a passage when the incident and policy use different terminology. The MVP mitigates this with a small curated corpus, visible retrieval results, representative evaluation cases, and straightforward tuning of headings, synonyms, and ranking.

### Hallucinated or misleading analysis

A schema-valid result can still be wrong. The MVP mitigates this by separating facts from inferences, constraining outputs, checking citations, applying deterministic rules, adding a review pass, and preserving human judgment.

### False confidence from the AI reviewer

The triage and review stages may use the same model and share blind spots. The reviewer is therefore a consistency check, not independent assurance, and its findings remain visible and non-authoritative.

### Prompt injection in incident or policy text

Incident reports and documents are treated as untrusted data rather than instructions. Prompts must delimit their content, and deterministic application logic must control permissions, schemas, citations, and action boundaries.

### Local model reliability and performance

Smaller local models may produce malformed output, weak reasoning, or slow responses. The MVP uses concise schemas and prompts, bounded context, explicit failure handling, and evaluation against the exact selected model.

### Sensitive data exposure

Local inference reduces external disclosure but does not make storage or logging automatically safe. The MVP should avoid unnecessary logging, avoid collecting secrets, and make local exports intentional.

### Stale or conflicting policies

Outdated guidance can produce grounded but incorrect recommendations. Policy metadata and visible citations help the user identify provenance; resolving policy governance is outside the MVP.

### Evaluation gives a misleading sense of quality

A small synthetic set cannot prove operational reliability. It provides a regression baseline and evidence for iteration, not a certification of safety or effectiveness.

## What we deliberately will not build

- Authentication, authorization roles, or multi-user collaboration.
- A production database or long-term case-management store.
- Integrations with SIEM, SOAR, EDR, IAM, ticketing, messaging, or cloud services.
- Live log ingestion, continuous monitoring, alerts, or event correlation.
- Autonomous agents, background tasks, or tool-using remediation workflows.
- Buttons that suspend accounts, revoke sessions, isolate hosts, delete data, or change access.
- An external vector database, knowledge graph, or distributed retrieval system.
- Model fine-tuning, training pipelines, or provider-agnostic model orchestration.
- A workflow engine or customizable playbook executor.
- Dashboards, fleet-wide analytics, executive reporting, or SLA tracking.
- Full forensic evidence collection, chain-of-custody management, or malware analysis.
- Automatic legal, privacy, breach-notification, or regulatory decisions.
- Policy authoring, approval, synchronization, or conflict resolution.
- Complex multi-agent architecture.

## Possible production additions

These are future options, not implied MVP commitments:

- Authentication, role-based access, and separation of analyst and approver duties.
- Encrypted incident persistence, retention controls, and tamper-evident audit logs.
- Multi-user case collaboration and an incident timeline.
- Policy lifecycle management, access controls, version comparison, and conflict detection.
- Hybrid lexical and embedding retrieval with local indexes and reranking.
- Carefully scoped read-only integrations for enriching incidents with internal evidence.
- Controlled ticketing or case-management integrations.
- Formal model and prompt versioning, evaluation dashboards, and quality monitoring.
- Independent reviewer models or rules for higher-assurance deployments.
- Organization-specific taxonomies, severity matrices, and approval policies.
- Export formats for established incident-response processes.
- Privacy controls such as field-level redaction and configurable logging.
- A separately designed, strongly authorized remediation workflow, only if a later product requirement justifies it; this would require additional security controls and is not a natural extension of MVP approval buttons.

Any production feature should preserve the central boundary: AI may organize evidence and recommend action, but accountable humans and deterministic controls govern consequential decisions.
