# Suspected Data Exfiltration Playbook

- Version: 1.0
- Owner: Fictional Data Protection Team
- Review date: 2026-09-03

> Fictional demonstration playbook. It does not represent the policy of any real company.

## Purpose

Guide initial triage of unusual copying, downloading, transfer, or disclosure of organizational data.

## Indicators

- Bulk download or export that is unusual for the user, role, device, or time of day.
- Access to customer, employee, financial, credential, or other sensitive records outside normal duties.
- Large outbound transfer, archive creation, removable-media use, or upload to an unapproved destination.
- Data access shortly after suspicious authentication, privilege escalation, or account recovery changes.
- Attempts to disable logging, bypass download controls, or delete transfer evidence.
- A third party reporting receipt of data that should not have been disclosed.

## Severity Guidance

- **Medium:** Unusual data access occurred, but transfer and sensitivity are not yet established.
- **High:** Likely unauthorized transfer of sensitive data, or an unexplained export of 1,000 or more customer or employee records.
- **Critical:** Confirmed external disclosure of highly restricted data, very large-scale extraction, or exfiltration with serious legal, safety, or operational impact.

Record count alone does not establish disclosure. The investigator must distinguish access, download, transfer, and confirmed external receipt.

## Recommended Actions

- Preserve audit records for access, query, export, download, and outbound transfer events.
- Determine the data type, approximate record count, sensitivity, destination, and business justification.
- Correlate the activity with account authentication, endpoint, proxy, and cloud-service evidence.
- Identify whether the data left an approved environment and whether any recipient is known.
- Recommend access restriction, session revocation, transfer blocking, or evidence preservation when ongoing loss is plausible.
- Escalate potential notification questions to authorized privacy or legal personnel without making a notification determination.

## Human Approval Requirements

Collection of existing read-only evidence requires a recorded human decision. Blocking transfers, disabling access, revoking sessions, isolating a device, contacting an external recipient, or notifying customers, regulators, law enforcement, or other third parties requires explicit authorized human approval. The copilot must not make legal conclusions or send notifications.
