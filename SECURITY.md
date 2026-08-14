# Security policy

## Reporting a vulnerability

Do not open a public issue for security-sensitive reports. Contact the repository owner privately through GitHub first and include only the minimum reproduction information required.

## Data and action policy

- Never include passwords, client secrets, access tokens, connection strings, production exports or unrestricted personal data in plugin inputs or generated artifacts.
- The quality-control pack detects common secret patterns and blocks the affected evidence input.
- Treat all D365, Azure DevOps, build and monitoring connectors as project-specific; begin read-only and require explicit owner approval for every write action.
- Generated code, mappings, tests, cutover plans and dashboards are review artifacts until independently validated in an approved target environment.
