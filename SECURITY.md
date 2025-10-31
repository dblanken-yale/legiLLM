# Security Policy

## Supported Versions

This project is currently in active development. Security updates will be provided for the latest version on the `main` branch.

| Version | Supported          |
| ------- | ------------------ |
| Latest (main branch) | :white_check_mark: |
| Older commits | :x: |

## Reporting a Vulnerability

We take the security of this project seriously. If you discover a security vulnerability, please follow these steps:

### How to Report

**Please do NOT create a public GitHub issue for security vulnerabilities.**

Instead, please report security issues by emailing:

**david.blankenship@yale.edu**

Please include:

1. **Description** of the vulnerability
2. **Steps to reproduce** the issue
3. **Potential impact** of the vulnerability
4. **Suggested fix** (if you have one)
5. **Your contact information** for follow-up questions

### What to Expect

- **Acknowledgment**: You will receive an acknowledgment of your report within 48 hours.
- **Updates**: We will provide regular updates on our progress addressing the vulnerability.
- **Timeline**: We aim to resolve critical vulnerabilities within 7 days and moderate issues within 30 days.
- **Credit**: With your permission, we will credit you in our security advisories and release notes.

## Security Best Practices for Users

When using this project, please follow these security guidelines:

### 1. API Keys and Secrets

- **Never commit** `.env` files or `config.json` to version control
- Store API keys in environment variables:
  - `PORTKEY_API_KEY` - Your Portkey API key
  - `LEGISCAN_API_KEY` - Your LegiScan API key
- Use Azure Key Vault or similar secret management for production deployments
- Rotate API keys regularly

### 2. Database Security

- Use strong passwords (20+ characters) for database credentials
- Enable SSL/TLS for database connections in production
- Restrict database network access using firewall rules
- Never use default credentials

### 3. Azure Deployment

- Enable managed identities for Azure resources
- Use Key Vault references for secrets in Container Apps
- Enable virtual network integration for production environments
- Review and apply Azure Security Center recommendations

### 4. Dependency Security

- Regularly update Python dependencies: `pip install -r requirements.txt --upgrade`
- Monitor for security advisories on dependencies
- Use `pip-audit` to check for known vulnerabilities:
  ```bash
  pip install pip-audit
  pip-audit
  ```

### 5. Data Privacy

- Be mindful that LegiScan data may contain personally identifiable information (PII) in bill text
- Review and comply with your organization's data retention policies
- Secure any exported data files appropriately

## Security Features

This project implements the following security measures:

- ✅ Environment-based secret management (no hardcoded credentials)
- ✅ Comprehensive `.gitignore` to prevent accidental secret commits
- ✅ Database connection pooling with parameterized queries (SQL injection prevention)
- ✅ Azure Key Vault integration for production deployments
- ✅ HTTPS enforcement for API communications
- ✅ Input validation for user-provided file paths and configuration

## Known Limitations

- This project is designed for internal research use and may require additional hardening for public-facing deployments
- Rate limiting for LegiScan API calls is implemented but should be monitored
- Audit logging is not currently implemented for database operations

## Security Audit History

- **2025-10-31**: Pre-public release security audit completed (see `docs/SECURITY_AUDIT_COMMIT.md`)
  - No sensitive data found in repository
  - All API keys properly managed via environment variables
  - Git history clean of credentials

## Questions?

If you have questions about security that don't relate to vulnerabilities, please open a regular GitHub issue or contact david.blankenship@yale.edu.

---

**Last Updated**: 2025-10-31
