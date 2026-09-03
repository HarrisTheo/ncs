# Triage Result Debugging Review

## Scope of this review

This review treats schema validity and a successful Ollama call as necessary but
not sufficient. It compares the first real `qwen3.5:9b` result with the incident
and the exact fictional policies supplied to the model.

Incident:

> An administrator account logged in from an unusual location, MFA was reset,
> and approximately 4,000 customer records were downloaded.

## Baseline result assessment

- **Evidence:** The unusual administrator login and 4,000-record download were
  directly supported. “MFA was reset for the administrator account” resolved an
  ambiguity that the incident did not explicitly resolve.
- **Recommendations:** Audit preservation and conditional session revocation
  were present in retrieved policy text. Their support was only described in
  generated rationale, not represented in a machine-checkable action field.
- **Severity:** `high` was plausible, but the explanation incorrectly reduced
  “an unexplained export of 1,000 or more records” to a record-count threshold.
  The input does not say the download was unexplained or unauthorized.
- **Policy references:** Filenames and section IDs existed in the supplied
  context. Membership alone did not prevent the model from misstating a rule.
- **Unsupported assumptions:** The result blurred unusual with unauthorized,
  download with export, and a reset with an unauthorized or unexpected reset.
- **Confidence:** `0.9` looked calibrated despite missing authorization,
  business-justification, transfer, destination, and impact facts.
- **Human readability:** The structure was understandable, but confident prose
  made policy qualifiers too easy to miss.

## Corrections

### 1. Evidence provenance

**BEFORE**

The model paraphrased evidence, including “MFA was reset for the administrator
account.” A later prompt iteration produced “Unexpected MFA reset.”

**PROBLEM**

Both statements add meaning not directly present in the incident. Schema-valid
text was being mistaken for source-grounded evidence.

**ROOT CAUSE**

`EvidenceItem` identified the source but did not prove that the observation
occurred in that source. Asking the 9B model to split and clean evidence also
created pressure to paraphrase.

**CHANGE**

The prompt now permits the complete incident as one evidence item, and the
orchestrator requires every evidence observation to be a normalized exact
substring of the submitted incident. Unsupported evidence rejects the run with
a visible diagnostic.

**AFTER**

The final run used the full incident verbatim as its single evidence item. Every
claim in the evidence collection is therefore directly supported, at the cost
of less granular evidence presentation.

### 2. Confidence representation

**BEFORE**

The result reported confidence `0.9`.

**PROBLEM**

No calibration data supports hundredths-level precision, and several material
facts were unknown. The number conveyed more certainty than the system earned.

**ROOT CAUSE**

The schema exposed a continuous `0.0`–`1.0` field, encouraging arbitrary numeric
precision, while the prompt only said to lower it when information was missing.

**CHANGE**

Confidence is now `low`, `medium`, or `high`, with concise prompt definitions.
Unknown authorization, causality, justification, impact, or transfer status
pushes the result toward low or medium.

**AFTER**

The final run returned `medium`. This is more honest and readable, though still
a model judgment rather than a calibrated probability.

### 3. Retrieval diversity

**BEFORE**

The top three section matches were data-exfiltration severity plus two
authentication sections. The relevant account-compromise playbook was omitted.

**PROBLEM**

Sections from one document competed with and displaced other relevant policy
documents, even though the model later needed their complete action and approval
guidance.

**ROOT CAUSE**

Retrieval ranked individual sections and then expanded only the documents that
won a top-three section slot.

**CHANGE**

TF-IDF now ranks complete documents, returns at most three, applies a small
relative floor of 25% of the best score, and supplies all sections from selected
documents. No embedding model or vector database was added.

**AFTER**

The final run retrieved, in order:

1. `authentication-security.md` — `0.1266`
2. `data-exfiltration.md` — `0.1116`
3. `account-compromise.md` — `0.0612`

The scores are corpus-relative similarities, not probabilities.

### 4. Policy citation accuracy

**BEFORE**

The model supplied valid section IDs but no exact application-resolved source
text. An attempted fix that asked it to quote policies caused it to join
non-adjacent bullets and insert ellipses while presenting the result as a quote.

**PROBLEM**

Valid identifiers did not make policy wording immediately auditable, while
model-generated quotations created a new hallucination surface.

**ROOT CAUSE**

Reproducing source text was incorrectly assigned to the LLM even though it is a
deterministic lookup operation.

**CHANGE**

The assessment returns only validated filename/section-ID pairs. The
orchestrator rejects nonexistent pairs and resolves accepted IDs to the exact
retrieved section text in `resolved_policy_references`.

**AFTER**

All three final references resolve exactly to real severity sections in the
authentication, account-compromise, and data-exfiltration documents. No model-
generated policy quotation is trusted or displayed as authoritative source text.

### 5. Recommendation grounding

**BEFORE**

Actions included free-form rationales and no structured action-to-policy link.
Later runs used rationales to assert unauthorized access or ongoing loss without
direct evidence.

**PROBLEM**

A plausible action could cite an unrelated valid section, and generated
rationale introduced new unsupported incident claims.

**ROOT CAUSE**

The action contract asked the model to both select policy guidance and explain
it, while deterministic validation checked neither the action text nor its
specific support.

**CHANGE**

Each action now carries one or more `policy_section_ids`; its text must be an
exact substring of at least one cited retrieved section. The unnecessary
free-form rationale field was removed. Policy conditions must remain in the
copied text.

**AFTER**

The final actions are exact policy bullets:

- Conditional session revocation or access restriction when active unauthorized
  access is plausible.
- Determine whether data left an approved environment and whether a recipient
  is known.

Both resolve to their stated action sections. The first retains its condition
instead of claiming that unauthorized access has been established.

### 6. Human-approval invariant

**BEFORE**

The prompt instructed the model to require approval, and an after-validation
check rejected `false`. One tightened-prompt run still emitted an action with
approval set to `false`.

**PROBLEM**

The value is a safety invariant, not a classification task, so giving the model
a boolean choice was unnecessary.

**ROOT CAUSE**

The JSON schema allowed both boolean values even though only `true` could pass
application validation.

**CHANGE**

`RecommendedAction.human_approval_required` is now typed as literal `true`.
Constrained generation and Pydantic agree on the only acceptable value.

**AFTER**

Both final recommendations and the top-level assessment require human approval.
The application still has no remediation tools or execution path.

### 7. Severity conditions and semantic overreach

**BEFORE**

The initial explanation treated 4,000 downloaded records as independently
satisfying the high-severity data rule and described ambiguous activity as
unauthorized.

**PROBLEM**

The policy requires likely unauthorized transfer or an unexplained export; it
also says record count alone does not establish disclosure. The incident does
not state authorization, justification, destination, external receipt, or
ongoing loss.

**ROOT CAUSE**

The prompt did not explicitly require every qualifier within a selected rule,
and the small model tends to collapse correlated suspicious indicators into a
confirmed narrative.

**CHANGE**

The prompt now distinguishes unusual from unauthorized, reset from unauthorized
reset, and download from external transfer. It requires material qualifiers,
prohibits combining weaker rules into a higher tier unless policy explicitly
does so, and asks that unknown facts remain unknown.

**AFTER**

The final result retains `high` with `medium` confidence. High is defensible as
a provisional triage rating under authentication guidance for suspicious use of
a privileged account, given the unusual sign-in, MFA change, and downstream
record access. It is **not** established by the data record count alone. The
generated summary correctly says external disclosure and material impact are
unconfirmed, but still calls the MFA reset “unexpected,” which the incident did
not literally state. This residual semantic embellishment remains a reviewer and
human-review concern; deterministic validation intentionally does not pretend to
be a general natural-language inference engine.

### 8. Complete and diagnosable output

**BEFORE**

One result ended `reasoning_summary` mid-sentence at the schema length boundary,
and malformed-response errors did not identify the failing fields.

**PROBLEM**

The assessment technically parsed but was confusing to a human, while later
failures were harder to debug than necessary.

**ROOT CAUSE**

The prompt had no practical summary-size target, the schema did not require a
complete sentence, and the Ollama wrapper collapsed Pydantic diagnostics into a
generic error.

**CHANGE**

The prompt requests at most two complete sentences and 450 characters. Pydantic
requires terminal punctuation. Provider errors now include validation locations
and messages while excluding raw model content.

**AFTER**

The final summary is two complete sentences and understandable to a human. The
system also failed visibly during intermediate reruns for unsupported evidence,
fabricated composite policy quotations, and an invalid approval flag rather than
silently manufacturing fallback assessments.

## Final result judgment

The final result is materially more credible than the baseline:

- All evidence fields are directly supported by the incident.
- Every policy reference names a real retrieved section and resolves to exact
  application-owned source text.
- Every recommendation is exact policy text linked to its source and requires
  human approval.
- `medium` confidence avoids misleading numeric precision.
- The output is concise and complete.

It is not proof of compromise or exfiltration. The provisional `high` severity
has a supportable authentication-policy interpretation, but the model's summary
still contains the unsupported adjective “unexpected.” The future reviewer
should flag this distinction, and the human must decide whether the high rating
is appropriate. A successful structured call remains a proposal, not a verified
decision.

## Verification performed

Command:

```text
.venv/bin/python -m pytest -q
```

Result: **81 passed**.

The example was rerun against local Ollama with `qwen3.5:9b`, thinking disabled,
temperature zero, and the Pydantic-generated structured-output schema. The final
run completed successfully. Intermediate rejected runs are described above
because those failures informed the final deterministic boundaries.
