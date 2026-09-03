# Authentication Security Policy

- Version: 1.0
- Owner: Fictional Identity Security Team
- Review date: 2026-09-03

> Fictional demonstration policy. It does not represent the policy of any real company.

## Purpose

Provide triage guidance for suspicious sign-ins, password attacks, multi-factor authentication (MFA) changes, and authentication control failures.

## Indicators

- Impossible travel or a sign-in from a country not previously associated with the account.
- Repeated failed sign-ins across one or many accounts, including password spraying.
- Successful sign-in shortly after many failures.
- Unexpected MFA reset, new MFA device, password reset, or recovery-method change.
- Privileged account authentication from an unmanaged device or anonymizing network.
- New session creation after credentials were reportedly changed.

## Severity Guidance

- **Low:** A small number of failed attempts with no successful access and no privileged target.
- **Medium:** Sustained password spraying, suspicious MFA prompts, or an unusual sign-in that has not been confirmed malicious.
- **High:** Successful suspicious access, an unauthorized MFA or recovery change, or suspicious use of a privileged account.
- **Critical:** Confirmed privileged access combined with security-control changes and evidence of material downstream impact.

## Recommended Actions

- Confirm sign-in time, source, device, user agent, and authentication result.
- Compare the activity with the user's known travel and device history.
- Review MFA, password, recovery-method, and session changes around the event.
- Identify resources accessed after the suspicious authentication.
- Recommend session revocation or temporary access restriction when active unauthorized access is plausible.

## Human Approval Requirements

An analyst may inspect existing authentication evidence after recording a human decision to proceed. Resetting credentials, revoking sessions, disabling an account, changing MFA, or restricting access requires explicit approval from an authorized human incident lead or identity administrator. The copilot must never perform these actions.
