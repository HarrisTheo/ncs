# Service Outage Triage Playbook

- Version: 1.0
- Owner: Fictional Reliability Team
- Review date: 2026-09-03

> Fictional demonstration playbook. It does not represent the policy of any real company.

## Purpose

Guide initial triage of degraded or unavailable applications, infrastructure, and customer-facing services.

## Indicators

- Health-check failures, elevated error rate, latency, timeout, or connection exhaustion.
- Customer reports that a service is unavailable or returning incorrect results.
- A sharp change after a deployment, configuration update, certificate change, or dependency failure.
- Resource saturation, queue growth, database connection pressure, or storage exhaustion.
- Multiple regions, tenants, or critical business workflows affected at the same time.
- Monitoring gaps that prevent confirmation of service health.

## Severity Guidance

- **Low:** Minor degradation with a workaround and no meaningful customer impact.
- **Medium:** Limited customer or internal impact, intermittent errors, or a non-critical component unavailable.
- **High:** Significant customer-facing degradation, a critical workflow unavailable, or impact continuing without a reliable workaround.
- **Critical:** Widespread outage, safety-related impact, severe data-integrity risk, or prolonged loss of a critical service.

Severity should be updated as scope, duration, workaround availability, and data-integrity impact become known.

## Recommended Actions

- Confirm affected service, start time, scope, error symptoms, and customer impact.
- Review recent deployments, configuration changes, capacity signals, and dependency health.
- Preserve relevant logs, metrics, traces, and change records.
- Identify a safe rollback, traffic shift, failover, or temporary mitigation for human consideration.
- Establish an update cadence and record unresolved questions about scope and cause.

## Human Approval Requirements

Reviewing existing telemetry requires a recorded human decision. Rollback, restart, failover, traffic change, configuration change, scaling, customer communication, or disabling a service requires explicit approval from an authorized human incident lead or service owner. The copilot must not modify production systems or publish status updates.
