# Pre-Demonstration Security Review

## Review scope

This review inspected the complete repository as implemented: Streamlit UI,
schemas, retrieval, prompts, Ollama adapter, triage and reviewer orchestration,
fictional policy corpus, evaluation runner and results, tests, configuration,
documentation, and repository hygiene.

The review assumes a local demonstration on a developer-controlled Mac. It does
not assume that a successful model call, valid JSON, a valid citation, or reviewer
approval makes a conclusion correct.

## Executive assessment

There is no Critical finding. The strongest existing safety property is
capability removal: the model has no tools, credentials, remediation API, shell,
or path supplied by the UI. Ollama is restricted to loopback, malformed outputs
fail closed, policy identifiers are checked, evidence must occur in the incident,
action text must occur in a cited policy section, and every generated action is
structurally marked for human approval.

Those controls prevent direct autonomous harm, but they do not establish
semantic correctness. The application is credible as a demonstration only if it
does not overstate what its deterministic checks or same-model reviewer prove.

The five most important weaknesses follow in priority order.

## 1. Policy-grounded text is not the same as an applicable recommendation

**Severity:** High

**Problem**

The deterministic grounding checks prove that evidence text occurs in the
incident, policy identifiers exist, and an action string occurs in a cited
policy section. They do not prove that the action's factual preconditions are
true, that the severity rule's qualifiers are satisfied, or that the free-form
reasoning summary is supported.

This is not hypothetical. The evaluation's sparse laptop report said no alert
was available, but triage recommended preserving the alert. The action was a
verbatim policy bullet and therefore passed deterministic validation. Earlier
runs also blurred unusual with unauthorized, reset with unexpected, and download
with exfiltration. The reviewer caught some examples but not reliably.

**Realistic consequence**

A human may receive a polished, cited recommendation that is impossible,
premature, or disproportionate to the reported facts. A copied containment
action can appear authoritative because its source is genuine even when its
condition is absent. In a time-sensitive incident, an analyst may act on the
recommendation before noticing the mismatch.

**Recommended fix**

For the MVP, make recommendation applicability explicit rather than attempting a
general rule engine:

- Distinguish investigation actions from conditional containment actions.
- Require every conditional action to retain a short, visible precondition and
  label whether that precondition is established or unknown.
- Display unknown preconditions beside the action, not only in summary prose.
- Add deterministic fixtures where a genuine policy action is inapplicable—for
  example, preserving a nonexistent alert or blocking a transfer that has ended.
- Treat unsupported summary claims or unmet action preconditions as a reviewer
  rejection that is prominent to the human.

Do not attempt to solve this by adding more unconstrained rationale text; prior
testing showed that generated rationales created additional unsupported claims.

**Implementation complexity:** Medium. This requires a small schema and prompt
change, UI rendering, and focused tests, but no new service or rule framework.

**MVP or future:** Necessary for a credible MVP demonstration. A comprehensive
machine-readable policy condition engine is reasonable future work and should
not be built now.

## 2. The documented Streamlit launch does not enforce the local privacy boundary

**Severity:** High

**Problem**

Ollama correctly rejects non-loopback hosts, but the repository does not pin
Streamlit to `127.0.0.1`. The README recommends `streamlit run app.py`, while
Streamlit's `server.address` remains unset. Depending on host and launch
environment, an unset bind address can make the unauthenticated app reachable
through non-loopback interfaces.

The UI accepts potentially sensitive incident narratives and retains the current
incident, assessment, retrieved context, and reviewer result in Streamlit session
memory. There is no authentication because this is intended to be local-only,
no explicit clear-session control, and no on-screen warning to use only synthetic
or sanitized incident data. The application itself does not intentionally write
incident content to disk, which is a useful existing control.

**Realistic consequence**

On a shared office, home, conference, or hotel network, another device could
potentially reach the application and view or submit incident information. A
demonstrator could also paste real customer, employee, credential, or operational
details under the mistaken belief that “local-first” means the UI is necessarily
private. Session data remains in process memory until the session or process is
cleared.

**Recommended fix**

- Add a checked-in Streamlit configuration that binds the server to
  `127.0.0.1`, and make the README launch command explicitly loopback-only.
- Keep CORS and XSRF protections enabled.
- Add a visible instruction to use synthetic or sanitized incident descriptions
  for the demonstration.
- Add a simple “Clear incident and results” control that removes relevant
  session-state values.
- Confirm that application logs and exception paths never emit raw incident,
  prompt, policy, or model-response content.

Authentication, encryption at rest, retention management, and multi-user
isolation should not be added to this local MVP; they become mandatory if the
application is ever intentionally exposed beyond loopback.

**Implementation complexity:** Low.

**MVP or future:** Loopback binding, sanitized-data notice, and session clearing
are necessary before demonstration. Authentication and durable-data controls are
future work for any non-local deployment.

## 3. Prompt injection and untrusted policy content are mitigated only by instructions

**Severity:** Medium

**Problem**

Both prompts say to treat the incident and policies as data, and JSON separates
them from the system prompt. That is useful but not a security boundary. There
are no adversarial tests showing how `qwen3.5:9b` behaves when an incident says
“ignore previous instructions,” embeds fake policy JSON, or asks the model to
approve an action.

The policy loader reads every Markdown file except `README.md` from the fixed
directory. It performs no allowlist, provenance/integrity check, maximum file or
section size check, required-heading validation, or suspicious-content audit.
All sections of each selected document are sent to both model calls. A stale,
accidentally edited, or malicious local document can therefore inject
instructions, alter action text, consume context, or create apparently valid
citations to bad guidance.

Because the app has no execution capability, prompt injection cannot directly
operate systems. It can still manipulate the security advice shown to a human.

**Realistic consequence**

A crafted incident or modified policy could cause the model to omit warnings,
inflate confidence, select unsafe actions, or make the reviewer approve the same
manipulated narrative. Policy citations would appear structurally valid because
the malicious content genuinely came from the loaded file.

**Recommended fix**

For the MVP:

- Load only an explicit manifest of the five expected policy filenames.
- Enforce small byte, section-count, and total-context limits and required
  headings before inference.
- Fail closed on unreadable or structurally invalid policy files.
- Add incident-injection and policy-injection evaluation cases, including fake
  JSON, fake system messages, and instructions to bypass approval.
- Keep the no-tools/no-remediation boundary; do not claim that text sanitization
  can reliably remove prompt injection.

For a production knowledge base, add controlled publishing, version approval,
access control, integrity metadata or signatures, and an audit trail.

**Implementation complexity:** Low to Medium for manifest, limits, and tests;
High for production policy governance.

**MVP or future:** Manifest/size validation and a few adversarial cases are
necessary for the demonstration. Cryptographic provenance and lifecycle
governance are reasonable future work.

## 4. The same-model reviewer creates an assurance signal stronger than its evidence

**Severity:** Medium

**Problem**

Triage and review normally use the same `OllamaLLM` instance and model. They share
training, prompt-following limitations, and likely blind spots. The UI nevertheless
uses strong labels such as “Reviewer accepted the assessment as grounded” and
“Passed” for factual and policy grounding.

The actual twelve-case evaluation produced eight approvals and four rejections.
Only one rejection clearly added value; three were likely false positives or
internally inconsistent. One reviewer demanded every policy action, another
objected to appropriately cautious uncertainty, and another rejected approval
handling while explaining that it was consistent. Reviewer statements can also
end mid-sentence at the 500-character field boundary.

The tests prove context construction, schema behavior, and preservation of the
original assessment. The deliberately bad deterministic test uses a controlled
stub response; it does not measure real-model detection reliability.

**Realistic consequence**

A human may interpret an approval and three “Passed” labels as independent
verification when it is only a second sample from the same fallible model.
Conversely, false rejections can distract the analyst, reduce trust in useful
warnings, or encourage repeated runs until a preferred answer appears.

**Recommended fix**

- Change UI language from “accepted as grounded” and “Passed” to “No issue
  detected by AI reviewer” and “Reviewer reported no issue.”
- State beside the result that the reviewer uses the same local model and is
  advisory, not independent assurance.
- Clarify in the reviewer prompt that policy action lists are not exhaustive and
  approval requirements may live in a different section of the same policy.
- Add a small labelled reviewer set containing both real errors and correct
  assessments, then report false-positive and detection counts separately.
- Prevent visibly truncated reviewer findings, either with shorter prompt limits
  or a completeness validator.

Do not add another agent framework. A genuinely independent model or deterministic
policy engine is future work only if measured risk justifies it.

**Implementation complexity:** Low for language, prompt, completeness, and test
changes; Medium or higher for independent assurance.

**MVP or future:** Honest UI language and reviewer regression cases are necessary
for the MVP. An independent reviewer model is reasonable future work.

## 5. Retrieval cannot reliably distinguish a relevant match from incidental vocabulary

**Severity:** Medium

**Problem**

Retrieval ranks all five documents with TF-IDF and keeps documents scoring at
least 25% of the best score. This is a relative threshold, not an evidence-based
minimum. Any incident sharing a few generic terms with the corpus can produce a
nonzero “best” document and proceed as grounded even when no policy is genuinely
applicable. Supplying every section of up to three documents also increases
irrelevant context and the chance that the model selects an attractive but
inapplicable action.

The 100% retrieval hit rate comes from twelve synthetic cases written close to
the policy vocabulary. Tests cover expected domains, empty directories, and
zero/invalid limits, but not unrelated incidents, synonym drift, conflicting
policies, malformed or oversized files, ranking stability after corpus changes,
or prompt-injected documents.

There is also no structured `insufficient_information` field. The evaluation
uses low confidence as a proxy and scored 0/1 on its one sparse case. Low model
confidence and weak retrieval are different failure modes but are currently
blurred in the human experience.

**Realistic consequence**

An out-of-domain or vague report may receive a confident-looking assessment
grounded in whichever policy happens to share generic words. The user sees
scores, but those scores are corpus-relative and may be mistaken for calibrated
relevance. A relevant policy may also fall below the relative floor after a
minor corpus edit.

**Recommended fix**

- Add several out-of-domain, weak-match, synonym, and corpus-change retrieval
  tests before choosing a conservative no-match rule.
- Establish a small empirically justified minimum-match or required-indicator
  criterion; return a visible “no reliable policy match” state when it fails.
- Keep raw similarity labelled as corpus-relative and do not present it as
  confidence.
- Add a structured insufficiency/unknowns signal so sparse evidence is not
  inferred from confidence prose or reviewer warnings.
- Continue using TF-IDF for five files; embeddings and a vector database would
  not solve policy applicability and are unnecessary here.

**Implementation complexity:** Low to Medium.

**MVP or future:** Negative retrieval tests, a conservative no-match behavior,
and an explicit insufficiency signal are necessary for a trustworthy demo.
Embedding retrieval or reranking is reasonable future work only after measured
lexical failures.

## Important controls already present

The following areas were reviewed but do not belong in the top five because the
current implementation handles them proportionately for a local MVP:

- **Fabricated citations:** filename/section pairs must exist in the exact
  retrieved context; arbitrary paths are rejected.
- **Malformed output:** Pydantic rejects wrong enums, fields, types, approval
  combinations, malformed JSON, empty responses, and incomplete triage summaries.
- **Human-approval flags:** every recommendation's flag is literal `true`, and
  the top-level flag must agree with action presence.
- **Autonomous remediation:** there is no execution path, operational connector,
  credential, or remediation button.
- **Ollama failures:** loopback-only host validation, timeouts, unavailable-model
  errors, malformed-response errors, and visible UI failure states exist.
- **Basic data persistence:** the app does not intentionally save incident text,
  prompts, or results to a database or project file.
- **Complexity:** the code remains small, synchronous, and understandable; adding
  an agent framework, vector database, workflow engine, or production datastore
  would worsen the MVP.

Human approval is structurally required but not recorded as a durable decision
in the current UI. Because the application cannot execute an action, this is not
a direct authorization bypass. The demonstration must describe the screen as a
decision-support artifact, not a complete approval or audit workflow. Recorded
approvals, role separation, and durable audit logs are future requirements for
any operational deployment.

## Recommended pre-demonstration order

If changes are authorized, the smallest risk-reduction sequence is:

1. Enforce loopback-only Streamlit and sanitized-data/session-clear controls.
2. Make action preconditions and insufficiency visible and test them.
3. Add policy manifest/size validation and prompt-injection cases.
4. Weaken reviewer assurance language and address known false-positive patterns.
5. Add weak-match retrieval tests and a conservative no-match rule.

This order does not require new infrastructure and preserves the small-project
constraint.
