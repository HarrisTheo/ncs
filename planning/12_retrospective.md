# Project Retrospective

## 1. Initial idea

The project began as a local-first **AI Incident Triage & Investigation
Copilot**. A user supplies a natural-language security or operational incident,
the application retrieves relevant internal guidance, produces a structured
triage proposal, validates it, asks a second model pass to review it, and leaves
the decision with a human:

> incident → retrieval → triage → verification → human decision

The intended value was faster, more consistent initial investigation—not a
complete Security Operations Center and not autonomous remediation.

## 2. Initial assumptions

The initial scope assumed one technical user, one incident at a time, a MacBook
M3 Pro, local Ollama inference, approximately five short curated Markdown
policies, and synthetic or sanitized incident data. It assumed a small local
model could usually follow a concise structured-output contract, while still
requiring explicit handling for malformed or incorrect output.

Some early product assumptions were broader than the implementation that was
eventually needed. The first scope discussed optional incident fields, separate
facts/inferences/unknowns, recorded recommendation dispositions, export, policy
metadata, repair attempts, and deterministic severity rules. Several of these
were later removed because they did not improve the core demonstration enough to
justify their cost.

## 3. Architecture proposed

The proposed architecture used Python and a thin Streamlit interface over a
UI-independent backend. Pydantic owned input and model-output contracts;
scikit-learn TF-IDF retrieved local policy text; an Ollama adapter isolated
provider-specific behavior; one model call proposed triage; deterministic code
validated schema, citations, evidence, actions, and approval flags; a second
model call reviewed the unchanged assessment; and a small pytest-based
evaluation harness exercised representative cases.

Keyword search, TF-IDF, and embedding retrieval were compared. TF-IDF with
cosine similarity was selected because it was transparent and sufficient for
five documents. No vector database, database, cloud service, agent framework,
or operational integration was introduced.

## 4. Architecture challenged before implementation

The pre-implementation review found that the design was drifting toward a small
platform. It challenged the number of modules and data models, the use of
“agent” language for two ordinary model requests, automatic repair, a general
severity-rule engine, action-impact classification, configurable indexing,
retrieval-threshold tuning, multiple export formats, a configuration subsystem,
and an evaluation application larger than the product itself.

The review also identified risks before code was written: prompt delimiters are
not a security boundary, local services can still be network-accessible,
downloads and logs can leak incident data, and an AI reviewer can create false
assurance. This review was useful, although the eventual implementation did not
adopt every proposed human-decision or export element from the revised design.

## 5. What was simplified

The implemented MVP reduced intake to one text area, used one in-memory TF-IDF
retriever, kept Ollama configuration to a model name and loopback host, removed
automatic repair, omitted a policy/severity rule engine, and used two bounded
model calls rather than autonomous agents. It did not add persistence, export,
policy administration, remediation controls, or a workflow engine.

During debugging, numeric confidence was replaced with `low`, `medium`, or
`high`; generated policy quotations were replaced by deterministic source
lookup; free-form action rationales were removed; and actions became exact text
linked to policy section identifiers. The final maintainability pass removed a
redundant approval check, avoided repeated normalization, clarified naming, and
removed a repeated evaluation calculation. The full suite then passed 90 tests.

## 6. How Codex helped with implementation

Codex turned the product definition into version-controlled planning documents,
inspected the local environment, scaffolded the small project, wrote five
fictional policies, and implemented each layer incrementally. It kept retrieval
independent from inference, isolated Ollama in `src/llm.py`, defined strict
Pydantic contracts, built grounded triage and advisory review orchestration,
added the Streamlit UI, and created deterministic tests plus a twelve-case real
pipeline evaluation.

It also inspected the available local-model options rather than silently
downloading one. After explicit approval, `qwen3.5:9b` was selected as a
practical 6.6 GB Q4 model for the available Apple Silicon memory. The model was
used with temperature zero, thinking disabled, an 8,192-token application
context, and Pydantic-generated JSON schemas.

## 7. How Codex helped with debugging

Codex did not stop at a successful API call. It ran the example incident,
inspected the retrieved documents, compared each evidence claim and action with
the original incident and policy text, and recorded discrepancies. It then made
small changes to prompts, schemas, context construction, retrieval, and
deterministic validation, rerunning both tests and real inference between
changes.

Several intermediate model runs failed visibly for unsupported evidence,
fabricated composite quotations, an invalid approval flag, and a truncated
summary. Those failures were used to tighten the boundary rather than being
hidden behind a fallback result.

## 8. One concrete weak or incorrect AI behavior discovered

In the first real triage result, the model reported “MFA was reset for the
administrator account.” The incident only said that an administrator logged in
from an unusual location and that MFA was reset; it did not explicitly identify
whose MFA was reset. A later prompt iteration changed this to “Unexpected MFA
reset,” adding a different unsupported qualifier.

The same baseline result gave confidence `0.9` despite unknown authorization,
business justification, transfer destination, and external disclosure. This
showed that valid JSON and plausible language were not sufficient evidence of a
grounded result.

## 9. How it was diagnosed

The diagnosis compared output fields directly with the submitted incident and
retrieved policy passages. The team separated literal evidence from reasonable
interpretation and checked every policy qualifier. That review found that the
schema recorded an evidence source but did not prove the observation occurred
in that source. It also found that a continuous confidence field invited
misleading precision without calibration data.

The wider evaluation confirmed the pattern. All twelve cases produced valid
structured triage and review outputs, but seven had at least one failure reason;
human-approval expectations passed only 9/12, and the sole insufficient-
information case was missed by the low-confidence proxy.

## 10. How it was corrected

Evidence observations were required to be normalized exact substrings of the
incident, with unsupported evidence rejecting the run. The prompt was allowed
to use the complete incident as one evidence item rather than forcing risky
paraphrasing. Confidence became a categorical value, and prompt guidance made
unknown authorization, causality, impact, and transfer status reasons to lower
confidence.

Related corrections made policy references application-resolved rather than
model-quoted, linked each recommendation to specific policy sections, required
action text to occur in a cited section, constrained every action approval flag
to literal `true`, and rejected incomplete reasoning summaries. This reduced
the known failure surface but did not solve semantic reasoning in general.

## 11. Security review findings

The pre-demonstration review found no Critical issue because the model has no
tools, credentials, remediation API, or operational connector. It identified
five leading weaknesses:

1. **High:** policy-cited actions can still be contextually inapplicable.
2. **High:** Streamlit was not explicitly bound to localhost.
3. **Medium:** prompt injection and untrusted policy content rely mainly on
   instruction-level mitigation.
4. **Medium:** a reviewer using the same model can imply stronger assurance than
   it provides.
5. **Medium:** lexical retrieval can confuse incidental vocabulary overlap with
   meaningful relevance.

The review also noted residual concerns around confidence interpretation,
sensitive incident data, model and retrieval failures, and test coverage. Some
of these are mitigated by fail-closed Pydantic validation, exact citation
membership checks, loopback-only Ollama, explicit failure states, no intentional
persistence, and removal of remediation capability.

## 12. Codex recommendations accepted

The accepted security recommendation was to enforce the local privacy boundary.
A checked-in `.streamlit/config.toml` now binds Streamlit to `127.0.0.1`, and the
README launch command repeats the loopback address explicitly. Startup output
confirmed `127.0.0.1`, the health endpoint returned `ok`, and the UI tests
continued to pass.

Earlier recommendations that were also accepted included using TF-IDF instead
of embeddings, using Pydantic at model boundaries, resolving citations
deterministically, making all proposed actions require human approval, isolating
Ollama-specific logic, avoiding repair loops, and keeping the system unable to
execute remediation.

## 13. Codex recommendations rejected or deferred

Security findings 1, 3, 4, and 5 were explicitly deferred: semantic action
preconditions, stronger prompt-injection and policy-content controls, reviewer
assurance changes, and stricter weak-match retrieval handling. The additional
issue-2 suggestions for a sanitized-data notice, session clearing, logging
checks, authentication, encryption, and retention controls were not added when
the decision was made to implement only localhost binding.

Broader scope ideas such as durable human-decision recording, exports, policy
governance, embedding retrieval, an independent reviewer model, and production
identity or audit controls also remain outside the implementation.

## 14. Why those decisions were made

Localhost binding was selected because it closed a concrete exposure risk with
a deterministic, low-complexity change that matched the local-first product
assumption. The other findings required changes across prompts, schemas,
retrieval, evaluation, UI semantics, or policy governance. They were not judged
appropriate after the MVP had been declared feature-complete.

Deferral does not mean the findings were disproved. It means the demonstration
must be presented honestly as advisory software using fictional policies, not
as an independently verified security decision system. Capability removal and
human judgment were favored over adding incomplete production controls.

## 15. Final technical trade-offs

- TF-IDF is simple, inspectable, and effective on the curated corpus, but weak
  on synonyms, out-of-domain input, and changing policy vocabulary.
- Document-level retrieval improves source diversity and supplies complete
  policy guidance, but includes irrelevant sections and uses a heuristic
  relative threshold.
- Exact substring grounding is deterministic and testable, but favors copied
  text and cannot determine whether a true policy statement applies to the
  incident.
- Categorical confidence avoids false numeric precision, but remains an
  uncalibrated model judgment.
- A second model pass can catch some errors, but the same local model also
  produced false positives and is not independent assurance.
- Local inference and loopback binding reduce disclosure, but do not provide
  production authentication, encrypted persistence, policy governance, or
  multi-user isolation.
- Synchronous, in-memory execution keeps the project understandable but is not
  intended for scale or durable case management.

## 16. Weakest part of the implementation

The weakest part is semantic applicability of recommendations. The application
can prove that an action was copied from a real retrieved policy section, but it
cannot prove that the action's preconditions are present. In the sparse laptop
evaluation case, it recommended preserving an alert even though the report
explicitly said no alert was available. The reviewer caught that example, but
its other three rejections were likely false positives, so it is not a reliable
substitute for deterministic applicability checks or human review.

## 17. What I would improve with another day

The next focused improvement would be to represent action preconditions and
insufficient information explicitly, without building a general rules engine.
Each conditional recommendation would retain its policy condition and show
whether that condition is established or unknown. Tests would cover genuine but
inapplicable policy actions, resolved-benign incidents, weak or unrelated
retrieval matches, and a few incident- and policy-based prompt-injection cases.

I would also calibrate the reviewer with a small labelled set that measures both
useful detections and false positives, and change its presentation so approval
means only that the AI reviewer found no issue—not that the assessment was
independently verified. These changes target failures observed in this project;
they would be more valuable than adding infrastructure or more features.
