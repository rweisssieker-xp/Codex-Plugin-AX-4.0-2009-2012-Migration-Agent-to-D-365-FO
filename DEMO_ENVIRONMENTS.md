# D365 F&O demo and development environments

The target metadata connector is deliberately import-based until an approved connector is configured. It accepts a sanitized metadata export and never stores credentials.

## Official Microsoft options

- A **free subscription-based F&O trial** can be provisioned through the Power Platform admin experience. Microsoft states that trial environments include demo data but do **not** support Visual Studio development. Use this for fit-to-standard, process and UAT demonstrations: [Unified admin trials](https://learn.microsoft.com/en-us/power-platform/admin/unified-experience/admin-trials).
- A **developer-focused sandbox / Tier-1 developer environment** is required for metadata work, Visual Studio, compilation and X++ test evidence. The development account needs the System Administrator role: [Install and configure development tools](https://learn.microsoft.com/en-us/power-platform/developer/unified-experience/finance-operations-install-config-tools).
- Microsoft documents demo data for Commerce, distribution, service, public sector and manufacturing scenarios. Deploy it only in a non-production environment: [F&O demo data overview](https://learn.microsoft.com/en-us/dynamics365/fin-ops-core/dev-itpro/get-started/demo-data).

## Plugin boundary

Do not put URLs, tenant IDs, client secrets, credentials, production exports or personal data into this plugin's generated output. Export only approved target metadata and build/test result summaries, then use the Enterprise Delivery Factory with those sanitized files.
