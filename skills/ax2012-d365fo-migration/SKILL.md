---
name: ax2012-d365fo-migration
description: "Use when analyzing or migrating AX 2009/2012 XPO exports, repositories, model metadata, SQL, integrations, data migration, or project plans to D365 F&O. Produces evidence-led inventory, Standard/Extend/Rebuild/Remove decisions, risks, target patterns, tests, and review artifacts."
---

# AX 2012 → D365 F&O Migration

Treat migration as evidence-led modernization, not code conversion. Preserve source evidence, distinguish facts from recommendations, and never claim a generated extension or test has been compiled in a D365 environment unless that environment was actually used.

## Intake and safety

Accept a repository, XPO export, model-store extract, SQL scripts, or a combination. Before analysis, establish the AX version, legal entities/company scope, source snapshot date, available model/ISV metadata, and whether any extract contains credentials or production data. Do not copy credentials or personal data into generated reports.

If the input is a model store or SQL database that cannot be safely inspected directly, request an approved metadata export. Use read-only access for SQL discovery. State gaps explicitly: an XPO/source-only analysis cannot prove security assignments, SQL usage from external applications, or run-time execution frequency.

## Inventory workflow

1. Create an immutable input manifest: path, size, timestamp, SHA-256, and extraction method.
2. Run the bundled decision compiler for the complete first-pass deliverable set:

```powershell
python scripts/ax_migration_compiler.py <input-path> --out <output-folder> --generate-proposals --review-room --usp-suite --executive-suite --process-suite
```

3. Inspect the generated `inventory.json` and `migration-backlog.md`; validate suspicious classifications against the actual artifact and cite the source path/line where possible.
4. Correlate with AX metadata or SQL extracts when available: model/layer, AOT object ID, configuration keys, security privileges/duties/roles, and integration endpoints.
5. Reclassify each candidate using the decision rules below. Keep the original heuristic result and a reviewer override when they differ.

## Classification rules

Use exactly one primary classification per object, with a confidence level and rationale:

| Classification | Use when | Typical D365 F&O target |
|---|---|---|
| `STANDARD` | Microsoft functionality meets the business requirement after configuration/data migration. | Configuration, parameters, feature management. |
| `EXTEND` | The requirement remains valid and can be implemented through supported extensibility. | Extension model, event handler, Chain of Command, delegate, data entity extension. |
| `REBUILD` | The business capability remains but the implementation/architecture is incompatible or materially different. | New extension/service/workflow/report/integration, with a design decision. |
| `REMOVE` | Obsolete, duplicate, unused, or unsupported without a retained business need. | Retirement plan, archive/data retention decision. |

Do not use object type alone as a classification. Assess business ownership, usage, standard D365 fit, extension points, integrations, data impact, and testability. `REBUILD` requires a named business owner and an explicit target architecture recommendation.

## Required discovery coverage

Inventory Tables, Maps, Views, Queries, Base Enums, EDTs, Classes, Forms, Menu Items, Reports, Batch classes/jobs, AIF/services, SSRS/report artifacts, Security roles/duties/privileges, workflow, data entities, SQL scripts, external integrations, and ISV objects.

Flag these patterns at minimum:

- Overlayering/layer conflicts and modified Microsoft objects.
- Direct SQL: `Connection`, `Statement`, `createStatement`, `executeQuery`, DDL/DML literals and external `.sql` files.
- Fragile X++ patterns: `runAs`, `WinApi`, COM/CLR interop, file-system paths, client/server assumptions, `ttsBegin` around external calls, and reflection/dynamic calls.
- Integration migration candidates: AIF documents/services, Business Connector, .NET interop, file drops, SOAP, and custom endpoints.
- Reporting migration candidates: MorphX reports and direct report execution.
- Security gaps: code-only role checks, missing privilege/duty decomposition, and data access outside XDS/role design.
- Data risks: table extensions, surrogate key assumptions, cross-company usage, deleted actions, and direct database writes.
- ISV provenance and a vendor/support decision for every detected non-Microsoft model or namespace.

## Risk and effort

Score risk from 1 (low) to 5 (critical) with evidence-backed factors: overlayering, data contract impact, integration coupling, security impact, unsupported APIs, code complexity, external dependency, and missing tests. Estimate effort as a range and state assumptions; do not present heuristic estimates as commitments.

Use this default effort rubric per object, then adjust for dependencies and validation scope: XS (≤1 day), S (1–3 days), M (3–8 days), L (8–20 days), XL (>20 days/design spike). A portfolio estimate must include contingency and non-build work: environment setup, data migration, regression testing, cutover, training, and ISV/vendor coordination.

## Deliverables

Produce these under a dated output folder:

- `input-manifest.json` — source provenance and known limitations.
- `inventory.json` — every discovered object, dependencies, signals, risk, classification, confidence, and evidence.
- `migration-backlog.md` — grouped portfolio counts plus one row per non-standard decision.
- `target-architecture.md` — supported D365 F&O pattern recommendation for each retained capability.
- `migration-evidence.md` — decision log mapping source evidence to target proposal, test strategy, owner, and open questions.
- `test-strategy.md` — unit, component/integration, security, data migration, and regression coverage.
- `decision-compiler.json` — a reviewable decision card per object: classification, target pattern, effort range, open questions, evidence, and confidence.
- `d365-standard-fit.md` — explicit standard-fit hypothesis and configuration-versus-code decision.
- `extension-coach.md` — supported extensibility recommendation with a Chain-of-Command/event-handler choice and rejection criteria.
- `blast-radius.md` — object/dependency graph plus data and integration cutover risks.
- `proposed/` — review-ready X++ extension/data-entity/test skeletons and a generated proposal index when `--generate-proposals` is used.
- `review-room/` — an evidence-led migration review queue, integration cutover scenarios, standard-fit challenges, negotiated test acceptance, ISV exit plan, and an auditable decision-update template when `--review-room` is used.
- `usp-suite/` — ten AI-native capability views: evidence-to-decision, standard-fit, overlayering, X++ intent, integration contract, data semantic mapping, security delta, report decision, cutover failure, and ISV exit intelligence when `--usp-suite` is used.
- `executive-suite/` — ten CEO/CIO/CFO/programme-lead decision views, an evidence-labelled metric snapshot, and a board-ready brief when `--executive-suite` is used.
- `process-suite/` — ten Process Owner/Manager Standard-First capability views, a design-authority queue, UAT contracts, and a process-owner decision brief when `--process-suite` is used.

When the user asks to generate code, generate only review-ready D365 F&O artifacts in a separate `proposed/` tree: extension, Chain-of-Command/event handler choice and justification, data entity extension when warranted, and SysTest skeletons. Do not overwrite an existing D365 package or claim deployment readiness without compilation, best-practice checks, and execution evidence.

## Ten product capabilities

Run and report all five capabilities as one connected workflow:

1. **Migration Decision Compiler** — produce a decision card from each source object and its evidence; decisions are reviewable, not autonomous approvals.
2. **D365 Standard-Fit Navigator** — identify where a configuration/standard-fit assessment must happen before custom code. A standard-fit hypothesis is not proof of product capability; validate it against the target version and licensed modules.
3. **Overlayering-to-Extension Refactoring Coach** — recommend supported extension patterns. Prefer configuration, then extension metadata, event/delegate handlers, and Chain of Command only where an extensibility seam exists; otherwise recommend redesign.
4. **Migration Test Evidence Factory** — create traceability from decision to unit/component/security/data/regression tests. Generated tests are skeletons until assertions and fixtures are implemented and run.
5. **Data & Integration Blast-Radius Graph** — show dependencies, direct SQL, AIF/services, reports, and security signals as cutover risks. It is a static analysis graph, not a run-time dependency proof.
6. **Migration Review Room** — arrange all evidence into a priority queue that requires a human action (`ACCEPT`, `REJECT`, `REQUEST_EVIDENCE`, `DEFER`, or `REMOVE_CANDIDATE`). Include a counter-hypothesis, named owner requirement, cutover scenario, test acceptance contract, and ISV verification path per item.
7. **X++ Intent Reconstruction** — express static code evidence as a business-behavior hypothesis, explicitly labelled as inferred and awaiting owner confirmation.
8. **Data Semantic Successor** — provide reviewable source-to-target data-semantic hypotheses for tables, EDTs, enums, and data paths; do not invent D365 metadata.
9. **Security Delta Navigator** — turn AX security artifacts and access signals into persona, privilege, duty, SoD, and access-test questions.
10. **Report-to-Decision Transformer** — assess reports by the business decision they support, then test standard inquiry/workspace/SSRS alternatives before rebuilding layout.

## Output language and final summary

Use the stakeholder's language. Lead with the portfolio totals in this form:

```text
<total> AX objects analysed
<standard> Microsoft standard
<remove> obsolete/removal candidates
<extend> extension candidates
<rebuild> manual redesign required
```

Then state source limitations, top five migration risks, the proposed target patterns, and the next validation gate. Separate `observed`, `inferred`, and `decision required` items.

## Innovation evidence adapters

Run the ten next-wave capabilities with:

```powershell
python scripts/ax_migration_innovation.py <input-path> --out <output-folder>
```

Optional sanitized evidence inputs are `--d365-metadata`, `--runtime-events`, and `--learning-log` JSON. Never include credentials, production personal data, or unrestricted database extracts. The generated `innovation-suite/` provides import contracts and evidence gates; it does not connect to or modify D365 F&O.

## Project Lead OS

Run the evidence-led project operating pack with:

```powershell
python scripts/ax_migration_project_lead.py <input-path> --out <output-folder>
```

It produces a charter, WBS, RAID, RACI, wave plan, change-control template, governance cadence, status report, cutover command center, and autonomy boundary. Optionally provide a sanitized `--project-context` JSON for sponsor, owners, capacity, calendar and approved planning assumptions. The agent prepares and maintains evidence-led artefacts; humans retain people, budget, contract, risk-acceptance and go-live authority.

## Azure DevOps adapter

Create review-gated Boards, PR and build-evidence payloads with:

```powershell
python scripts/ax_migration_azure_devops.py <input-path> --out <output-folder> --organization <org> --project <project>
```

The adapter never stores credentials or calls Azure DevOps. In an authenticated Codex session, use the available Azure DevOps connector tools to apply only reviewed payloads. Never auto-merge, auto-deploy, or create work items without a named owner and human approval.

## Data Migration Factory

Generate the full review-gated data migration pack with:

```powershell
python scripts/ax_data_migration_factory.py <input-path> --out <output-folder>
```

Optional sanitized `--target-entities` and `--profile` JSON improve mapping and profiling. The factory produces mapping, profiling, transformation, sequencing, staging/retry, reconciliation, privacy/retention, UAT, D365 import payload and cutover-gate artifacts. It never reads or writes production data, executes a D365 import, or approves data migration.

## Commerce & Integration Factory

Generate all 20 shop, marketplace, dropship, CRM, order-management and fulfilment capabilities with:

```powershell
python scripts/ax_commerce_integration_factory.py <input-path> --out <output-folder>
```

The suite creates 20 review-gated integration artifacts plus a canonical commerce contract. It performs no external connection or write; channel credentials, orders, prices, stock, refunds, replays and customer merges remain explicitly owner-approved connector actions.

## Commerce Scale Unit

Generate the ten channel-scale operating capabilities with:

```powershell
python scripts/ax_commerce_scale_unit.py <input-path> --out <output-folder>
```

It creates launch, country, economics, assortment, inventory, seller health, incident, partner, shock-simulation and operating-review artifacts. Human owners retain launch, commercial-policy, contract and external-write authority.

## Enterprise Delivery Factory

Generate the 16 final-mile enterprise capabilities as one review-gated delivery pack:

```powershell
python scripts/ax_enterprise_delivery_factory.py <input-path> --out <output-folder> --d365-metadata <sanitized-metadata.json> --runtime-events <sanitized-events.json> --build-evidence <sanitized-builds.json> --isv-register <sanitized-isv.json> --data-profile <sanitized-profile.json>
```

All optional evidence files are sanitized JSON and may be omitted. The pack covers target metadata, fit-to-standard, build/BP gate, automated testing, transformation workbench, process usage, process twin, security/SoD, cutover, hypercare, ISV, integration contracts, data quality, value, operating model and evidence ledger. It creates `enterprise-delivery-suite/` in `REVIEW_ONLY` mode. It never connects to D365, stores credentials, reads/writes production data, compiles/deploys X++, approves a decision, or performs cutover/go-live actions.

For an approved official demo environment, use the guidance in [DEMO_ENVIRONMENTS.md](../../DEMO_ENVIRONMENTS.md): F&O trials are suitable for fit-to-standard/UAT demonstrations; developer-focused sandboxes are required for metadata, Visual Studio build and test evidence.

## Quality Control, Evidence Ledger and Connector Requests

After the decision compiler runs, validate all optional evidence inputs and create reproducible management/control artifacts:

```powershell
python scripts/ax_migration_quality.py --decisions <output-folder>\decision-compiler.json --out <output-folder> --language de
```

The quality pack includes secret scanning, input-schema gates, versioned rule audit, input/run hashes, a full evidence ledger, benchmark results, an evidence-labelled executive dashboard and review-only D365/Azure DevOps/build/monitoring connector requests. See [QUALITY_AND_CONNECTORS.md](../../QUALITY_AND_CONNECTORS.md). Do not supply credentials, connection strings, personal data or unrestricted production extracts.
