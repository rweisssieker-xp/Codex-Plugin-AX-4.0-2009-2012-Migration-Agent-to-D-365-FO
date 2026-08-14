#!/usr/bin/env python3
"""Generate review-gated enterprise delivery artifacts for AX to D365 F&O.

No connector, build, import, deployment, approval, or production operation is run.
Optional JSON files must be sanitized and contain no credentials or personal data.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from ax_migration_compiler import decision_cards, markdown_table, safe_name
from ax_migration_inventory import discover


CAPABILITIES = [
    (
        "01-d365-target-metadata-connector",
        "D365 Target Metadata Connector",
        "Compare supplied target metadata with migration candidates; produce only verified, missing and evidence-gap results.",
    ),
    (
        "02-fit-to-standard-copilot",
        "Fit-to-Standard Copilot",
        "Turn every retained capability into a configuration-versus-extension decision gate with a named Process Owner.",
    ),
    (
        "03-xpp-build-best-practice-gate",
        "X++ Build & Best-Practice Gate",
        "Prepare a build evidence contract for reviewable packages, compilation and best-practice outcomes.",
    ),
    (
        "04-automated-test-lab",
        "Automated Test Lab",
        "Generate traceability for SysTest, RSAT, integration, security and UAT acceptance evidence.",
    ),
    (
        "05-code-transformation-workbench",
        "Code Transformation Workbench",
        "Prepare reviewed extension, event-handler, Chain-of-Command and data-entity work packets; no target code is applied.",
    ),
    (
        "06-process-mining-usage-evidence",
        "Process Mining & Usage Evidence",
        "Aggregate supplied runtime/process events to validate whether AX behavior is used; static source is never usage proof.",
    ),
    (
        "07-d365-process-twin",
        "D365 Process Twin",
        "Link AX evidence, target hypothesis, owner, control, data object and test acceptance for each process candidate.",
    ),
    (
        "08-security-sod-simulator",
        "Security & SoD Simulator",
        "Create persona, duty, privilege, segregation-of-duties and access-test review questions from AX security evidence.",
    ),
    (
        "09-cutover-orchestrator",
        "Cutover Orchestrator",
        "Build a reversible cutover runbook with sequencing, named gates, rollback and communications templates.",
    ),
    (
        "10-hypercare-command-center",
        "Hypercare Command Center",
        "Prepare monitoring, triage, reconciliation, incident and executive-review artifacts without operating telemetry.",
    ),
    (
        "11-isv-compatibility-intelligence",
        "ISV Compatibility Intelligence",
        "Track vendor/model provenance, support decision, contract dependency and exit-path evidence.",
    ),
    (
        "12-integration-contract-testing",
        "Integration Contract Testing",
        "Create contract, schema-drift, replay, idempotency, error-path and performance test obligations.",
    ),
    (
        "13-data-quality-remediation-loop",
        "Data Quality Remediation Loop",
        "Turn profiling and reconciliation gaps into owner-assigned cleansing and evidence gates.",
    ),
    (
        "14-value-benefits-realization",
        "Value & Benefits Realization",
        "Expose cost, risk, standardization benefit and operating impact as assumptions awaiting finance/business validation.",
    ),
    (
        "15-operating-model-enablement",
        "Operating Model & Enablement",
        "Prepare governance, design authority, ALM, support, training and handover decisions.",
    ),
    (
        "16-evidence-ledger-audit-trail",
        "Evidence Ledger & Audit Trail",
        "Create a traceable record from AX source through decision, approval, build, test and deployment evidence.",
    ),
]


def load_records(path: Path | None, keys: tuple[str, ...]) -> list[dict]:
    if not path:
        return []
    if not path.exists():
        raise SystemExit(f"Evidence file does not exist: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in keys:
            if isinstance(value.get(key), list):
                return [item for item in value[key] if isinstance(item, dict)]
    return []


def write_markdown(
    path: Path,
    title: str,
    boundary: str,
    rows: list[dict],
    columns: list[tuple[str, str]],
) -> None:
    lines = [f"# {title}", "", boundary, "", "## Evidence status", ""]
    if rows:
        lines.extend(markdown_table(rows, columns))
    else:
        lines.append(
            "No matching sanitized evidence was supplied. This is an evidence gap, not a claim that the capability is absent or ready."
        )
    lines.extend(
        [
            "",
            "## Mandatory human gate",
            "",
            "A named accountable owner must review the evidence, select the decision, and record approval or rejection.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate 16 enterprise migration delivery suites."
    )
    parser.add_argument("input", type=Path, help="AX source directory or export")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--d365-metadata",
        type=Path,
        help="Sanitized objects: name/type/extensionPoints",
    )
    parser.add_argument(
        "--runtime-events",
        type=Path,
        help="Sanitized aggregates: process/eventType/company/count",
    )
    parser.add_argument(
        "--build-evidence", type=Path, help="Sanitized build/test evidence; no secrets"
    )
    parser.add_argument(
        "--isv-register", type=Path, help="Sanitized ISV/model/vendor register"
    )
    parser.add_argument(
        "--data-profile",
        type=Path,
        help="Sanitized data-quality profile and exceptions",
    )
    args = parser.parse_args()
    if not args.input.exists():
        parser.error(f"Input does not exist: {args.input}")

    cards = decision_cards(discover(args.input))
    metadata = load_records(args.d365_metadata, ("objects", "metadata", "items"))
    events = load_records(args.runtime_events, ("events", "items"))
    builds = load_records(args.build_evidence, ("builds", "tests", "items"))
    isvs = load_records(args.isv_register, ("vendors", "models", "items"))
    profile = load_records(args.data_profile, ("tables", "exceptions", "items"))
    root = args.out / "enterprise-delivery-suite"
    root.mkdir(parents=True, exist_ok=True)
    metadata_names = {str(item.get("name", "")).lower() for item in metadata}
    retained = [card for card in cards if card["decision"] in {"EXTEND", "REBUILD"}]

    target_rows = [
        {
            "object": c["object"],
            "type": c["type"],
            "metadata": (
                "VERIFIED" if c["object"].lower() in metadata_names else "UNVERIFIED"
            ),
            "next": "Validate target feature and extensibility seam",
        }
        for c in retained
    ]
    write_markdown(
        root / "01-d365-target-metadata-connector.md",
        CAPABILITIES[0][1],
        "Uses supplied, sanitized metadata only. A D365 F&O connection is never opened by this generator.",
        target_rows,
        [
            ("AX object", "object"),
            ("Type", "type"),
            ("Target metadata", "metadata"),
            ("Next gate", "next"),
        ],
    )

    standard_rows = [
        {
            "capability": c["object"],
            "proposal": c["targetPattern"],
            "decision": "STANDARD-FIT REVIEW",
            "owner": "UNASSIGNED",
        }
        for c in retained
    ]
    write_markdown(
        root / "02-fit-to-standard-copilot.md",
        CAPABILITIES[1][1],
        "A standard-fit hypothesis is not proof of licensed D365 capability; validate product version, modules and configuration.",
        standard_rows,
        [
            ("Capability", "capability"),
            ("Target proposal", "proposal"),
            ("Gate", "decision"),
            ("Owner", "owner"),
        ],
    )

    build_rows = [
        {
            "candidate": c["object"],
            "package": "REVIEW_ONLY",
            "build": "PENDING approved sandbox build",
            "test": "PENDING executed evidence",
        }
        for c in retained
    ]
    write_markdown(
        root / "03-xpp-build-best-practice-gate.md",
        CAPABILITIES[2][1],
        "Build records are imported evidence only. This plugin does not compile, deploy, or alter a D365 package.",
        build_rows + builds,
        [
            ("Candidate", "candidate"),
            ("Package", "package"),
            ("Build", "build"),
            ("Test", "test"),
        ],
    )

    test_rows = [
        {
            "object": c["object"],
            "tests": "SysTest; RSAT/UAT; integration/security/data as applicable",
            "acceptance": "Process Owner approval plus executed target evidence",
        }
        for c in retained
    ]
    write_markdown(
        root / "04-automated-test-lab.md",
        CAPABILITIES[3][1],
        "Generated test scope is a test design. Fixtures, assertions, target execution and approval are required separately.",
        test_rows,
        [
            ("Object", "object"),
            ("Required coverage", "tests"),
            ("Acceptance", "acceptance"),
        ],
    )

    transform_rows = [
        {
            "object": c["object"],
            "pattern": c["targetPattern"],
            "workPacket": "Extension/CoC/event/data entity design review",
            "status": "NO CODE APPLIED",
        }
        for c in retained
    ]
    write_markdown(
        root / "05-code-transformation-workbench.md",
        CAPABILITIES[4][1],
        "No source or target package is overwritten. A developer must review, compile and test any proposed transformation.",
        transform_rows,
        [
            ("Object", "object"),
            ("Pattern", "pattern"),
            ("Work packet", "workPacket"),
            ("Status", "status"),
        ],
    )

    event_counts = Counter(
        str(item.get("process", item.get("eventType", "UNCLASSIFIED")))
        for item in events
    )
    usage_rows = [
        {
            "process/event": key,
            "count": value,
            "claim": "Imported aggregate evidence; validate source and period",
        }
        for key, value in event_counts.most_common()
    ]
    write_markdown(
        root / "06-process-mining-usage-evidence.md",
        CAPABILITIES[5][1],
        "Only supplied aggregate events are counted. No AX, SQL or telemetry connection is made.",
        usage_rows,
        [("Process/event", "process/event"), ("Count", "count"), ("Boundary", "claim")],
    )

    twin_rows = [
        {
            "process": safe_name(c["object"]),
            "target": c["targetPattern"],
            "data/control": "Confirm entity, persona and control",
            "acceptance": "Owner-approved scenario",
        }
        for c in retained
    ]
    write_markdown(
        root / "07-d365-process-twin.md",
        CAPABILITIES[6][1],
        "Process relationships are inferred from static AX evidence until Process Owner confirmation.",
        twin_rows,
        [
            ("Process candidate", "process"),
            ("Target", "target"),
            ("Data/control", "data/control"),
            ("Acceptance", "acceptance"),
        ],
    )

    security_rows = [
        {
            "object": c["object"],
            "signal": ", ".join(c["signals"]) or "security review",
            "review": "Persona, duty, privilege, XDS and SoD test",
            "status": "UNVERIFIED",
        }
        for c in cards
        if "Security" in c["type"]
        or c["type"] in {"SecurityRole", "SecurityDuty", "SecurityPrivilege"}
    ]
    write_markdown(
        root / "08-security-sod-simulator.md",
        CAPABILITIES[7][1],
        "Static AX roles cannot prove D365 entitlement or segregation-of-duties outcomes.",
        security_rows,
        [
            ("AX artifact", "object"),
            ("Signal", "signal"),
            ("Required review", "review"),
            ("Status", "status"),
        ],
    )

    cutover_rows = [
        {
            "sequence": "1",
            "gate": "Reconciliation baseline and rollback validated",
            "owner": "Data Migration Lead",
            "decision": "GO/NO-GO",
        },
        {
            "sequence": "2",
            "gate": "Integration, security and business smoke tests passed",
            "owner": "Test Lead",
            "decision": "GO/NO-GO",
        },
        {
            "sequence": "3",
            "gate": "Business authorization and communications complete",
            "owner": "Sponsor",
            "decision": "GO/NO-GO",
        },
    ]
    write_markdown(
        root / "09-cutover-orchestrator.md",
        CAPABILITIES[8][1],
        "Runbook template only. Human cutover authority, rollback ownership and production execution remain mandatory.",
        cutover_rows,
        [
            ("Sequence", "sequence"),
            ("Gate", "gate"),
            ("Owner", "owner"),
            ("Decision", "decision"),
        ],
    )

    hypercare_rows = [
        {
            "domain": "Integration",
            "signal": "Failure, replay queue, schema drift",
            "owner": "UNASSIGNED",
            "response": "Triage, reconcile, decide rollback",
        },
        {
            "domain": "Data",
            "signal": "Balance/key/count mismatch",
            "owner": "UNASSIGNED",
            "response": "Freeze, reconcile, approve correction",
        },
        {
            "domain": "Process",
            "signal": "UAT or adoption failure",
            "owner": "UNASSIGNED",
            "response": "Incident and owner decision",
        },
    ]
    write_markdown(
        root / "10-hypercare-command-center.md",
        CAPABILITIES[9][1],
        "Monitoring configuration and operational actions require approved external telemetry connectors.",
        hypercare_rows,
        [
            ("Domain", "domain"),
            ("Signal", "signal"),
            ("Owner", "owner"),
            ("Response", "response"),
        ],
    )

    isv_rows = isvs or [
        {
            "model": c["object"],
            "vendor": "UNKNOWN",
            "support": "Validate contract/support/upgrade path",
            "exit": "Document replacement or retention decision",
        }
        for c in cards
        if "isv" in " ".join(c["signals"]).lower()
    ]
    write_markdown(
        root / "11-isv-compatibility-intelligence.md",
        CAPABILITIES[10][1],
        "Vendor and support claims must be verified against current contracts and release documentation.",
        isv_rows,
        [
            ("Model", "model"),
            ("Vendor", "vendor"),
            ("Support", "support"),
            ("Exit path", "exit"),
        ],
    )

    contract_rows = [
        {
            "object": c["object"],
            "contract": "API/schema/version/error/replay/idempotency/performance",
            "status": "CONSUMER AND OWNER REQUIRED",
        }
        for c in cards
        if any(s in c["signals"] for s in ("aif_or_service", "direct_sql"))
    ]
    write_markdown(
        root / "12-integration-contract-testing.md",
        CAPABILITIES[11][1],
        "The generator never calls an endpoint, sends a message or replays production payloads.",
        contract_rows,
        [
            ("Object", "object"),
            ("Contract obligations", "contract"),
            ("Status", "status"),
        ],
    )

    quality_rows = profile or [
        {
            "object": c["object"],
            "risk": "Profile completeness, duplicates, references, keys and balances",
            "owner": "Data Owner",
            "exit": "Approved reconciliation exception register",
        }
        for c in cards
        if c["type"] == "Table"
    ]
    write_markdown(
        root / "13-data-quality-remediation-loop.md",
        CAPABILITIES[12][1],
        "No production data is read or changed. Profiling and remediation need approved data access and owner approval.",
        quality_rows,
        [("Object", "object"), ("Risk", "risk"), ("Owner", "owner"), ("Exit", "exit")],
    )

    value_rows = [
        {
            "object": c["object"],
            "effort": c["effort"],
            "risk": c["risk"],
            "benefit": "Validate standardization, operating cost and business value",
            "status": "ASSUMPTION",
        }
        for c in retained
    ]
    write_markdown(
        root / "14-value-benefits-realization.md",
        CAPABILITIES[13][1],
        "Effort and benefit are planning assumptions, not commitments, forecasts or financial advice.",
        value_rows,
        [
            ("Object", "object"),
            ("Effort", "effort"),
            ("Risk", "risk"),
            ("Benefit", "benefit"),
            ("Status", "status"),
        ],
    )

    operating_rows = [
        {
            "area": "Design Authority",
            "decision": "Standard/extend/rebuild/remove governance",
            "owner": "Solution Architect",
        },
        {
            "area": "ALM",
            "decision": "Branch, build, test, release and evidence policy",
            "owner": "Engineering Lead",
        },
        {
            "area": "Enablement",
            "decision": "Training, support model and business handover",
            "owner": "Change Lead",
        },
    ]
    write_markdown(
        root / "15-operating-model-enablement.md",
        CAPABILITIES[14][1],
        "Role assignments and operating policies require programme approval.",
        operating_rows,
        [("Area", "area"), ("Decision", "decision"), ("Owner", "owner")],
    )

    ledger_rows = [
        {
            "object": c["object"],
            "source": "; ".join(c["evidence"]),
            "decision": c["decision"],
            "required": "Owner decision; target metadata; build; test; deployment evidence",
        }
        for c in cards
    ]
    write_markdown(
        root / "16-evidence-ledger-audit-trail.md",
        CAPABILITIES[15][1],
        "This is a review traceability register, not an immutable audit system or compliance certification.",
        ledger_rows,
        [
            ("Object", "object"),
            ("Source evidence", "source"),
            ("Decision", "decision"),
            ("Required closure", "required"),
        ],
    )

    catalog = [
        {
            "id": key,
            "title": title,
            "outcome": outcome,
            "mode": "REVIEW_GATED",
            "metric": "Evidence-complete owner decisions",
            "killCondition": "Stop/replace if five qualified reviews do not reduce decision cycle time or rework",
        }
        for key, title, outcome in CAPABILITIES
    ]
    (root / "enterprise-delivery-catalog.json").write_text(
        json.dumps(
            {
                "schemaVersion": "1.0",
                "mode": "REVIEW_ONLY",
                "capabilities": catalog,
                "imports": {
                    "d365Metadata": len(metadata),
                    "runtimeEvents": len(events),
                    "buildEvidence": len(builds),
                    "isvRecords": len(isvs),
                    "dataProfile": len(profile),
                },
                "humanOnly": [
                    "Connect target environments",
                    "Read or write production data",
                    "Compile/deploy packages",
                    "Approve fit, risk, budget, cutover or go-live",
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(root),
                "capabilities": len(CAPABILITIES),
                "objectsAnalysed": len(cards),
            }
        )
    )


if __name__ == "__main__":
    main()
