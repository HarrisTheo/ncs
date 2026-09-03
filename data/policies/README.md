# Local policy corpus

This directory contains a small, curated Markdown knowledge base used only to demonstrate local retrieval and grounded incident triage.

All documents in this directory are fictional. They do not represent the policies, controls, or recommendations of any real company.

The demonstration corpus contains:

- `authentication-security.md`
- `account-compromise.md`
- `data-exfiltration.md`
- `malware-response.md`
- `service-outage.md`

Each document should follow this minimal convention:

```markdown
# Document title

- Version: 1.0
- Owner: Example team
- Review date: YYYY-MM-DD

## Stable section heading

Policy or playbook text.
```

Passage identifiers will be generated from the file name and section heading. Documents are reference data, never executable instructions.
