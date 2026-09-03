# Human Decisions

## Decision: restrict Streamlit to localhost

**Issue:** The Streamlit server address was not explicitly configured. An
environment-dependent non-loopback bind could expose the unauthenticated
demonstration UI—and incident text entered into it—to other devices on the local
network.

**Decision:** Address security-review issue #2 for this MVP by checking in a
Streamlit configuration that binds the server to `127.0.0.1`. The documented
launch command also supplies the same address explicitly. No authentication,
session-management, logging, or other security features are being added.

**Why this fix was selected:** It closes a concrete privacy-boundary gap with a
small, deterministic configuration change. It matches the product's local-first
scope and can be verified without changing the application pipeline.

**Why the other issues are deferred:** Issues #1, #3, #4, and #5 concern semantic
recommendation applicability, prompt injection and policy trust, reviewer
independence, and retrieval confidence. They remain documented in
`planning/09_security_review.md` as known limitations and future improvements.
Addressing them would require prompt, schema, retrieval, evaluation, or UI
behavior changes beyond the narrowly approved localhost fix. The demonstration
must continue to be presented as advisory, policy-grounded assistance rather
than a complete or independently verified security decision system.
