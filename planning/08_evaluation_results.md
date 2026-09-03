# Evaluation Results

## Run configuration

- Date: 2026-09-03
- Model: `qwen3.5:9b`
- Cases: 12 synthetic cases from `evals/cases.json`
- Policies: five fictional local Markdown policies
- Inference: local Ollama, temperature zero, thinking disabled
- Pipeline: retrieval → triage → validation → reviewer
- Retries: none

Command, using the project virtual environment's `python`:

```text
python evals/run_eval.py
```

The concrete interpreter path used for this run was `.venv/bin/python`.

## Metric definitions

The definitions were fixed before running the cases:

- **Successful structured output:** both `IncidentAssessment` and
  `ReviewerResult` were returned and passed Pydantic validation. Reviewer
  rejection still counts as structured-output success.
- **Category accuracy:** exact structured category match among valid triage
  outputs.
- **Severity accuracy:** structured severity belongs to the case's predefined
  acceptable set among valid triage outputs.
- **Policy retrieval hit:** all predefined required policy sources appear in the
  deterministic retrieved document set. This is separate from model citation.
- **Human-approval compliance:** the top-level flag equals the predefined
  expectation and every generated action requires approval.
- **Insufficient-information handling:** for cases predefined as insufficient,
  the current structural proxy requires `confidence == "low"`. No generated
  phrase is matched.
- **Failed case:** any expected-property miss, pipeline failure, or reviewer
  rejection. A reviewer rejection can therefore reveal either a real triage
  problem or an overcritical reviewer.

Expected values were not changed after observing the run.

## Aggregate results

| Metric | Result |
|---|---:|
| Total cases | 12 |
| Successful structured outputs | 12/12 |
| Structured-output success rate | 100.0% |
| Triage structured outputs | 12/12 |
| Category accuracy | 12/12 (100.0%) |
| Severity accuracy | 12/12 (100.0%) |
| Policy retrieval hit rate | 12/12 (100.0%) |
| Human-approval compliance | 9/12 (75.0%) |
| Insufficient-information handling | 0/1 (0.0%) |
| Reviewer approved | 8 |
| Reviewer rejected | 4 |
| Reviewer failed | 0 |
| Reviewer not run | 0 |
| Cases with at least one failure reason | 7/12 |

The perfect category, severity, and retrieval results are encouraging regression
signals only. Twelve curated examples are far too few to imply general accuracy.

## Failed cases and likely causes

### `auth_failed_attempts_benign`

Actual category and severity were correct and the reviewer approved. The case
failed because `human_approval_required` was `true`, while the fixed expectation
was `false`.

Likely cause: the triage model selected an investigative policy action even
though the incident already supplied benign confirmation. Because every action
must require approval, any unnecessary action turns the top-level flag on. The
prompt is stronger on policy support than on deciding when no further action is
needed.

### `auth_authorized_travel`

Actual category and severity were correct and the reviewer approved. The case
failed because `human_approval_required` was `true` instead of the expected
`false`.

Likely cause: the same action-selection bias appeared on a resolved-benign
unusual-location event. Retrieval correctly found authentication guidance, but
the model appears to equate having relevant recommended-action text with needing
to recommend an action.

### `auth_password_spray_no_success`

Category, medium severity, retrieval, and approval behavior matched expected
properties. The reviewer rejected the assessment because it included only one
authentication action and omitted the other actions listed by the policy.

Likely cause: this is probably a reviewer false positive. The policy action list
is a menu, not a mandatory checklist, and the reviewer was instructed to verify
the proposal rather than expand it. The reviewer prompt does not state explicitly
that a grounded assessment may select a relevant subset of actions.

### `account_compromise_confirmed_standard_user`

Category, high severity, retrieval, and approval behavior matched expectations.
The reviewer rejected the assessment after objecting to uncertainty language in
the reasoning summary, even while acknowledging that persistence on a standard
account satisfies the high-severity policy rule.

Likely cause: the reviewer treated a cautious statement that authorization or
malicious intent remained unconfirmed as an unsupported inference rather than a
limitation. This is an internally inconsistent rejection and demonstrates that
the same local model is not an independent verifier. The returned concern also
ended mid-sentence at the reviewer statement length limit.

### `data_exfiltration_confirmed_external_disclosure`

Category, critical severity, retrieval, and approval behavior matched expected
properties. The reviewer rejected the assessment while simultaneously explaining
that the evidence-preservation action's approval flag was consistent with the
separate Human Approval Requirements section.

Likely cause: the reviewer expected approval wording to appear in the same
Recommended Actions section as the action, rather than applying the retrieved
document's separate approval section. This is another likely reviewer false
positive. Its concern was also truncated at the statement length boundary.

### `malware_blocked_before_execution`

Category and low severity were correct and the reviewer approved. The case
failed because `human_approval_required` was `false`, while the fixed expectation
was `true`.

Likely cause: the model recommended no further action because the executable was
already blocked and review found no related activity. The expected value assumes
that preserving or reviewing endpoint evidence remains useful and requires a
recorded decision. This exposes a genuine ambiguity in whether the evaluation
property means “approval for any useful next step” or only “approval for actions
the model actually chose.” The expected value is retained unchanged.

### `ambiguous_laptop_popup_sparse_report`

The model returned the expected malware category and an acceptable low severity,
but confidence was `medium`; the fixed insufficiency proxy required `low`. The
reviewer also rejected the assessment because it recommended preserving an
alert even though the incident explicitly said no alert was available.

Likely causes:

- The confidence rubric allows medium when the observation and policy match are
  clear, even if corroborating evidence is sparse. That conflicts with the
  evaluation's deliberately strict low-confidence proxy.
- The action contract guarantees that an action is copied from policy, but does
  not prove that the referenced artifact exists in the incident. The reviewer
  correctly detected this semantic precondition failure.

This was the most informative failure: retrieval and schema grounding both
passed, yet the selected action was impossible under the reported facts.

## Reviewer outcome interpretation

The reviewer approved eight cases and rejected four. The four rejections were:

- Password spraying: likely false positive caused by demanding exhaustive
  policy actions.
- Standard-account compromise: likely false positive caused by treating stated
  uncertainty as an unsupported claim.
- Confirmed external disclosure: likely false positive caused by failing to
  combine the action and approval sections of one policy.
- Sparse laptop report: useful rejection of an inapplicable action.

The reviewer therefore added value in at least one case but also reduced the
clean-case count through inconsistent interpretations. Reviewer rejection should
remain visible as a separate diagnostic, not be treated as ground truth.

## What the run shows

Strengths:

- All 24 potential structured stages completed without malformed JSON, timeout,
  or provider failure.
- TF-IDF document retrieval found every required policy in this curated set.
- Category and severity stayed within all predefined expectations.
- Deterministic schemas maintained approval on every action that existed.

Weaknesses:

- The triage model recommends unnecessary investigation on resolved-benign
  authentication cases.
- Whether no-action outputs comply with “human approval required” is sensitive
  to how the expected property is defined.
- Sparse-information detection is not represented directly in the schema, and
  the low-confidence proxy failed its only positive case.
- Exact policy action copying does not guarantee that the action's factual
  prerequisites exist.
- Reviewer prose can be truncated and reviewer judgments can be internally
  inconsistent.

## Constraints on interpretation

These results must not be read as 100% real-world category or severity accuracy.
The dataset is small, synthetic, written using vocabulary close to the policies,
and evaluated once on one local model build. It does not measure repeatability,
calibration, adversarial robustness, real incident language, policy conflict,
or production fitness.

The main useful result is diagnostic: the structured pipeline is reliable on
this run, retrieval works for the curated corpus, and the next quality work
should focus on optional-action selection, action preconditions, explicit
insufficiency representation, and reviewer false positives—not on changing the
expected labels to make the aggregate score look better.
