# Account Compromise Playbook

- Version: 1.0
- Owner: Fictional Incident Response Team
- Review date: 2026-09-03

> Fictional demonstration playbook. It does not represent the policy of any real company.

## Purpose

Guide initial investigation when an account may be controlled or used by an unauthorized person.

## Indicators

- User denial of activity recorded under their identity.
- Unfamiliar sign-in source followed by successful access to internal resources.
- Unexpected password, MFA, recovery-method, API token, or SSH key changes.
- New mailbox forwarding rules, delegated access, or persistence mechanisms.
- Privilege elevation, creation of additional accounts, or use of dormant credentials.
- Activity continuing after the legitimate user signs out or changes a password.

## Severity Guidance

- **Medium:** Credible suspicious activity exists, but successful unauthorized access is not established.
- **High:** Unauthorized access is likely or confirmed, or persistence was created on a standard account.
- **Critical:** A privileged account is confirmed compromised, multiple accounts are affected, or the compromise causes material data loss or service impact.

Severity should reflect observed impact as well as account privilege. Suspicion alone must not be described as confirmed compromise.

## Recommended Actions

- Build a timeline of authentication, credential changes, privilege changes, and resource access.
- Confirm the activity with the account owner through a trusted channel.
- Identify active sessions, tokens, keys, delegated permissions, and newly created persistence.
- Review related accounts and systems for reuse of the same source, device, or credential.
- Recommend containment such as session revocation, credential reset, token removal, or account suspension when justified.

## Human Approval Requirements

Evidence review and user contact require a recorded human decision. Account suspension, session or token revocation, credential reset, removal of persistence, privilege reduction, and changes to another user's resources require explicit approval from an authorized human. The copilot provides recommendations only and must not initiate containment.
