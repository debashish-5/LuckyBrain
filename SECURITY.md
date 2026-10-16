# Security Policy

LuckyBrain is in early development and has not been security-certified. Do not
use it to process sensitive data in production without independently reviewing
the code, provider settings, and every integration in your application.

## Protecting your data and credentials

- Never commit API keys, passwords, tokens, private prompts, or sensitive
  datasets. Use environment variables for local development and a secret manager
  in deployed environments.
- Do not paste credentials, personal information, or customer data into public
  issues, pull requests, logs, or example code.
- Review which prompts, documents, and media are sent to external providers,
  what those providers retain, and what your application records in logs and
  traces.
- Treat retrieved content, uploaded files, model responses, and tool inputs as
  untrusted. Use least-privilege credentials, validate inputs, and constrain
  actions performed by integrations.

## Reporting a vulnerability

Please do not disclose suspected vulnerabilities in a public issue. Report
them privately through GitHub's **Report a vulnerability** feature for this
repository when it is enabled. Include affected versions or commits, impact,
and reproduction steps when safe to share.

Do not include real credentials, personal data, or customer data in a report.
If private reporting is unavailable, contact a repository maintainer directly
and request a secure channel. Maintainers will acknowledge reports and
coordinate investigation, remediation, and disclosure.
