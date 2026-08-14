# AX 4.0 / 2009 / 2012 → D365 F&O Migration Agent

> Turn AX customizations into evidence-led D365 Finance & Operations decisions, delivery plans, review artifacts and controlled implementation proposals.

This Codex plugin is not an X++ code converter. It is an end-to-end migration operating system for AX 4.0, AX 2009 and AX 2012 estates: discovery, standard-first classification, target architecture, data/integration risk, programme governance, test evidence, cutover readiness and post-go-live control.

## Why it exists

AX-to-D365 migrations fail when teams treat every customization as code to port. The real task is to decide which business capabilities should be adopted as standard, configured, extended, redesigned or retired—and to preserve the evidence behind every decision.

```text
AX XPO / Repository / SQL / Metadata / ISV evidence
                        ↓
              Static discovery and evidence graph
                        ↓
      STANDARD | EXTEND | REBUILD | REMOVE
                        ↓
 D365 target hypothesis + owner gates + test/data/security evidence
                        ↓
   Review-ready delivery, cutover and operating artifacts
```

## Who it helps

| Role | Decision support |
|---|---|
| Migration architect | Portfolio decisions, target patterns, extension seams, technical debt and ISV risk |
| Functional architect / Process Owner | Fit-to-standard, configuration-first challenge, UAT contracts and process authority queue |
| X++ / D365 developer | Review-ready extension, event/CoC and SysTest skeletons with explicit validation gaps |
| Data migration lead | Entity/mapping hypotheses, profiling, reconciliation, sequencing, staging and cutover controls |
| Integration lead | AIF/service/direct-SQL discovery, contract migration, consumer evidence, replay and error-handling gates |
| Security architect | Persona, role/duty/privilege, SoD and access-test decision artifacts |
| Project lead / PMO | Charter, WBS, RAID, RACI, wave plan, change control, governance cadence and status pack |
| CIO / CEO / CFO / Board | Evidence-labelled risk, value, scope, ISV, cutover and investment decision views |
| Commerce lead | Shop, marketplace, CRM, dropship, order-management and Commerce Scale Unit readiness |

## Core capabilities

### 1. AX discovery and migration decision compiler

Discovers and classifies Tables, EDTs, Enums, Maps, Views, Queries, Classes, Forms, Menu Items, Reports, batch classes/jobs, AIF/services, security artifacts, SQL scripts, external integrations and ISV hints.

It flags direct SQL, overlayering/layer evidence gaps, client/legacy APIs, COM/CLR/file-system assumptions, batch/cross-company patterns, reports, service contracts, security concerns and data risks. Every object receives evidence, risk, effort band, target hypothesis, confidence and an explicit reviewer gate.

```powershell
python scripts/ax_migration_compiler.py <AX-export-or-source> --out <output-folder> `
  --generate-proposals --review-room --usp-suite --executive-suite --process-suite
```

Main output: `inventory.json`, `decision-compiler.json`, `migration-backlog.md`, `d365-standard-fit.md`, `extension-coach.md`, `test-strategy.md` and `input-manifest.json`.

### 2. Standard-first and extension guidance

The decision model is deliberately opinionated:

1. Adopt D365 standard.
2. Configure.
3. Extend through supported metadata/events/delegates.
4. Use Chain of Command only at a verified extensibility seam.
5. Rebuild only after validated alternatives fail.
6. Retire capabilities without retained business usage.

The plugin never claims that a D365 feature, module, table, entity or extension point exists until target metadata and the applicable version/licence are verified.

### 3. Review room and generated development proposals

`--review-room` produces a priority queue for `ACCEPT`, `REJECT`, `REQUEST_EVIDENCE`, `DEFER` or `REMOVE_CANDIDATE`, including counter-hypotheses, owner requirements, ISV verification and required test/security/data evidence.

`--generate-proposals` creates a separate `proposed/` tree with review-ready migration designs and SysTest skeletons. These are **not** compiled, deployed or production-ready code.

### 4. Ten migration innovation capabilities

The innovation suite adds:

1. D365 Metadata & Extensibility Oracle
2. Runtime Process Mining Connector
3. Data Migration Reconciliation Twin
4. Golden-Process Regression Factory
5. Extension-Point Proof Engine
6. Hypercare Sentinel
7. Process Variant Elimination Engine
8. Regulatory & Audit Evidence Pack
9. Migration Learning Memory
10. Multi-Wave Portfolio Optimizer

```powershell
python scripts/ax_migration_innovation.py <AX-export> --out <output-folder> `
  --d365-metadata <sanitized-metadata.json> `
  --runtime-events <sanitized-events.json> `
  --learning-log <sanitized-decisions.json>
```

### 5. Project Lead OS

Generates a project operating pack that supports the work a programme/project lead must orchestrate:

- project charter and scope basis
- work-breakdown structure and integrated migration waves
- RAID log, RACI and ownership gaps
- change-control template
- governance cadence and weekly evidence-labelled status report
- cutover command centre and autonomy boundary

```powershell
python scripts/ax_migration_project_lead.py <AX-export> --out <output-folder> `
  --project-context <sanitized-project-context.json>
```

It prepares decisions and communications; people management, budget, contracts, formal risk acceptance and go-live remain human authority.

### 6. Azure DevOps review-payload adapter

Creates review-gated payloads for Boards, pull requests and build evidence. It is intentionally not an unattended work-item, merge or deployment bot.

```powershell
python scripts/ax_migration_azure_devops.py <AX-export> --out <output-folder> `
  --organization <organization> --project <project>
```

Apply a payload only through an approved, authenticated connector session and only with a named owner.

### 7. Data Migration Factory

Creates a data migration delivery pack covering mapping, profiling, transformation, sequencing, staging/retry, reconciliation, privacy/retention, UAT, import payloads and cutover gates.

```powershell
python scripts/ax_data_migration_factory.py <AX-export> --out <output-folder> `
  --target-entities <sanitized-target-entities.json> `
  --profile <sanitized-data-profile.json>
```

No production data is read, transformed or imported by the plugin.

### 8. Commerce and integration factory

Produces 20 review-gated capabilities for shops, marketplaces, dropship, CRM, order-management, fulfilment, EDI, inventory, pricing, refunds and partner onboarding.

```powershell
python scripts/ax_commerce_integration_factory.py <AX-export> --out <output-folder>
```

### 9. Commerce Scale Unit operating pack

Creates ten enterprise commerce operating views: launch factory, country readiness, economics, assortment, inventory allocation, seller health, incident command, partner blueprints, shock simulation and operating review.

```powershell
python scripts/ax_commerce_scale_unit.py <AX-export> --out <output-folder>
```

### 10. Enterprise Delivery Factory

The final-mile pack generates 16 capabilities:

1. target metadata connector
2. fit-to-standard copilot
3. X++ build and best-practice gate
4. automated test lab
5. code transformation workbench
6. process mining and usage evidence
7. D365 process twin
8. security and SoD simulator
9. cutover orchestrator
10. hypercare command centre
11. ISV compatibility intelligence
12. integration contract testing
13. data-quality remediation loop
14. value and benefits realisation
15. operating model and enablement
16. evidence ledger and audit trail

```powershell
python scripts/ax_enterprise_delivery_factory.py <AX-export> --out <output-folder> `
  --d365-metadata <sanitized-metadata.json> `
  --runtime-events <sanitized-events.json> `
  --build-evidence <sanitized-build-evidence.json> `
  --isv-register <sanitized-isv-register.json> `
  --data-profile <sanitized-data-profile.json>
```

### 11. Quality Control, reproducibility and benchmarks

The quality pack validates optional evidence, scans common secret/connection-string patterns, applies versioned rule audit, produces input/run hashes, creates an evidence ledger and executive dashboard, emits connector requests, and executes the bundled benchmark cases.

```powershell
python scripts/ax_migration_quality.py `
  --decisions <output-folder>\decision-compiler.json `
  --out <output-folder> `
  --language de
```

Schemas are supplied for D365 metadata, runtime events, build evidence, ISV register and data profile. See [QUALITY_AND_CONNECTORS.md](QUALITY_AND_CONNECTORS.md).

## D365 demo, sandbox and target-system evidence

Use a Microsoft F&O trial with demo data for fit-to-standard, demos and UAT. Use a developer-focused sandbox for target metadata, Visual Studio, X++ build and test evidence. See [DEMO_ENVIRONMENTS.md](DEMO_ENVIRONMENTS.md).

## Security and action boundaries

The plugin is evidence-led and `REVIEW_ONLY` by default. It never:

- stores credentials, access tokens or connection strings;
- connects to D365, SQL, Azure DevOps or monitoring without an approved connector;
- reads/writes production data;
- compiles or deploys X++;
- creates work items, PRs, merges or deployments autonomously;
- approves architecture, security, budget, cutover or go-live.

Every external action requires authenticated project access, a named owner and explicit human approval. Review [SECURITY.md](SECURITY.md), [PRIVACY.md](PRIVACY.md) and [TERMS.md](TERMS.md) before use with sensitive systems.

## Install and validate

Install from a configured Codex marketplace:

```powershell
codex plugin add ax2012-d365fo-migration-agent@codex-marketplace-global
```

Validate source changes:

```powershell
python -m unittest discover -s tests
python -m black --check scripts tests
python C:\Users\reinerw\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .
```

## Marketplace readiness

The plugin includes a Codex manifest, security/privacy/terms documents, support route, Apache-2.0 licence, tests, secret scanning, documented connector boundaries and a restricted-pilot checklist. See [MARKETPLACE_READINESS.md](MARKETPLACE_READINESS.md).

## Contributing, support and licence

- [Contributing guide](CONTRIBUTING.md)
- [Security policy](SECURITY.md)
- [Apache-2.0 licence](LICENSE)
- [GitHub Issues](https://github.com/rweisssieker-xp/Codex-Plugin-AX-4.0-2009-2012-Migration-Agent-to-D-365-FO/issues)

Never attach credentials, production data or personal data to issues, sample files or generated artifacts.
