# Security

LuckyBrain is alpha software and is **not** a security certification. Review
the package, provider integrations, and your application before using them
with sensitive or production workloads.

## Report a vulnerability privately

Please do not publish exploitable details in a public issue. Use GitHub's
[private vulnerability reporting](https://github.com/debashish-5/LuckyBrain/security/advisories/new)
for this repository. Include the affected version or commit, impact, and
reproduction details where safe. Allow maintainers reasonable time to
investigate and coordinate a fix before public disclosure.

## Secure use

- Keep provider credentials out of source control, browser code, and logs.
- Minimize sensitive data sent to external model providers.
- Treat external text and model output as untrusted input.
- Validate inputs and constrain side effects in custom tools and adapters.
- Review [production-readiness guidance](guides/production-readiness.md) and
  the repository's [security policy](https://github.com/debashish-5/LuckyBrain/blob/main/SECURITY.md).
