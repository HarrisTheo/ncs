# Evaluation Dataset Design

## Purpose

`evals/cases.json` contains twelve fictional, synthetic cases for evaluating the
observable behavior of the local pipeline. It does not prescribe generated
sentences. Each case defines properties that can later be checked against
structured output:

- Expected category.
- An acceptable severity set.
- One or more policy sources that must be retrieved or cited.
- Whether at least one recommendation—and therefore human approval—is expected.
- Whether the report is too sparse to support a confident conclusion.

The `notes` field documents why an expectation exists, but should not be used as
an exact-text assertion by the future runner.

## How the cases were chosen

The set is intentionally small but uses contrasts that reveal common model
errors better than twelve unrelated stories.

### Authentication contrasts

- Three failed attempts confirmed as benign test false-positive resistance.
- Authorized travel tests whether unusual geography is incorrectly equated with
  malicious access.
- An unusual sign-in plus an unconfirmed MFA change tests whether the model
  preserves unknown authorization.
- Password spraying with no successful access tests a direct medium-severity
  policy rule and whether success is invented.

### Confirmation and severity contrasts

- A standard account with user denial and persistence tests high-severity
  compromise.
- A confirmed privileged compromise with persistence and material impact tests
  the explicit critical boundary.
- A 400-record download with unknown destination tests the distinction between
  access, download, transfer, and disclosure.
- Confirmed external receipt of highly restricted records tests the critical
  data-disclosure boundary.
- Malware blocked before execution is paired with confirmed execution,
  persistence, and command-and-control activity.
- A customer-facing outage without a workaround exercises the operational
  playbook and guards against forcing every case into a security category.

### Sparse information

The final laptop pop-up report deliberately lacks telemetry, timing, execution,
and corroboration. It should remain low or medium severity and explicitly expose
insufficient information rather than manufacture a malware infection narrative.

## Failure modes exercised

The cases are designed to expose:

- False positives on benign authentication events.
- Failure to distinguish suspicious activity from confirmed unauthorized use.
- Severity inflation or suppression at explicit policy boundaries.
- Dropped qualifiers such as `confirmed`, `unexplained`, `external`, `blocked`,
  and `no workaround`.
- Confusion between download and exfiltration or external disclosure.
- Confusion between blocked malware and confirmed execution.
- Incorrect policy retrieval or fabricated policy references.
- Recommendations without the required human-approval flag.
- Confident conclusions from sparse evidence.
- Unsupported root-cause or impact claims in cross-domain incidents.

## Property interpretation

`acceptable_severities` is a set because policy application can contain genuine
judgment at category boundaries. A result passes this property when its
structured severity belongs to the set; no generated wording is compared.

`required_policy_sources` means every listed source is expected to appear in the
retrieved or cited policy set, depending on the later metric definition. The
runner should report retrieval coverage and citation coverage separately rather
than treating them as the same behavior.

`human_approval_required` describes the expected top-level structured flag. A
`true` value generally means the supplied facts support at least one useful
policy action. The two resolved-benign authentication cases expect no additional
recommendation and therefore `false` under the current schema invariant.

`insufficient_information_expected` is not an exact phrase requirement. The
current assessment schema has no dedicated insufficiency boolean, so a later
runner must define a structural proxy before scoring it—for example low
confidence combined with reviewer acceptance or a reviewer warning about
missing evidence. This metric should remain separately reported because any
proxy will be imperfect.

## What this dataset cannot establish

Twelve synthetic examples cannot meaningfully measure:

- Statistical accuracy, recall, precision, or calibrated confidence.
- Performance on real organizational language, telemetry, or policy conflicts.
- Generalization to incident types absent from the five-document corpus.
- Robustness to prompt injection, malformed policy files, very long reports, or
  deliberate adversarial evasion.
- Fairness across users, languages, regions, or writing styles.
- Stability across Ollama, model, quantization, or prompt versions without
  repeated runs.
- The independent reliability of the reviewer when it uses the same local model.
- Whether recommended actions are operationally correct for a real company.
- Production latency, concurrency, resource use, privacy, or security posture.

The dataset is a regression-oriented behavioral sample, not a benchmark. Its
main value is making expected policy distinctions explicit and detecting obvious
quality regressions as prompts, retrieval, schemas, or models change.

## Deliberate exclusions

No evaluation runner, scoring framework, model invocation, golden prose, or
snapshot output was added in this step. The dataset remains human-readable JSON
that the next implementation step can consume without introducing evaluation
infrastructure prematurely.
