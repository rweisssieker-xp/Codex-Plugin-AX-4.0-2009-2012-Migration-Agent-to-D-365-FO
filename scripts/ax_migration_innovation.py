#!/usr/bin/env python3
"""Innovation suite: evidence adapters and review artifacts for AX→D365 migration.

All outputs are advisory. Imported metadata and telemetry are retained only as aggregate
evidence in the output; do not provide secrets or production personal data.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from ax_migration_inventory import discover
from ax_migration_compiler import (
    decision_cards,
    markdown_table,
    review_priority,
    safe_name,
)


def load_json(path: Path | None) -> object:
    if not path:
        return []
    if not path.exists():
        raise SystemExit(f"Optional evidence file does not exist: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def as_list(value: object, keys: tuple[str, ...]) -> list[dict]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        for key in keys:
            if isinstance(value.get(key), list):
                return [item for item in value[key] if isinstance(item, dict)]
    return []


def write(
    path: Path,
    title: str,
    boundary: str,
    rows: list[dict],
    columns: list[tuple[str, str]],
) -> None:
    lines = [f"# {title}", "", boundary, ""]
    if rows:
        lines += markdown_table(rows, columns)
    else:
        lines += [
            "No matching evidence was supplied. This is a required evidence gap, not proof that the capability or risk is absent."
        ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate ten evidence-led innovation artifacts."
    )
    parser.add_argument("input", type=Path, help="AX source directory or export")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--d365-metadata",
        type=Path,
        help="Optional sanitized JSON list/objects with name/type",
    )
    parser.add_argument(
        "--runtime-events",
        type=Path,
        help="Optional sanitized JSON events; eventType/process/company/timestamp only",
    )
    parser.add_argument(
        "--learning-log",
        type=Path,
        help="Optional JSON reviewer decisions; no personal/sensitive data",
    )
    args = parser.parse_args()
    if not args.input.exists():
        parser.error(f"Input does not exist: {args.input}")
    cards = decision_cards(discover(args.input))
    metadata = as_list(load_json(args.d365_metadata), ("objects", "metadata", "items"))
    events = as_list(load_json(args.runtime_events), ("events", "items"))
    learning = as_list(load_json(args.learning_log), ("decisions", "feedback", "items"))
    suite = args.out / "innovation-suite"
    suite.mkdir(parents=True, exist_ok=True)
    names = {str(x.get("name", "")).lower() for x in metadata}
    matches = [
        {
            "object": c["object"],
            "type": c["type"],
            "metadata": "MATCH" if c["object"].lower() in names else "UNVERIFIED",
            "next": "Validate supported target and extension seam",
        }
        for c in cards
    ]
    write(
        suite / "01-d365-metadata-extensibility-oracle.md",
        "D365 Metadata & Extensibility Oracle",
        "Matches only supplied, sanitized D365 metadata. No connection to a D365 environment is attempted.",
        matches,
        [
            ("AX object", "object"),
            ("Type", "type"),
            ("Target metadata", "metadata"),
            ("Next gate", "next"),
        ],
    )
    event_counts = Counter(
        str(e.get("eventType", e.get("process", "UNCLASSIFIED"))) for e in events
    )
    write(
        suite / "02-runtime-process-mining.md",
        "Runtime Process Mining Connector",
        "Uses only supplied aggregate events; static AX source cannot prove runtime usage.",
        [
            {"event": k, "count": v, "evidence": "imported runtime event"}
            for k, v in event_counts.most_common()
        ],
        [("Event/process", "event"), ("Count", "count"), ("Evidence", "evidence")],
    )
    reconciliation = [
        {
            "object": c["object"],
            "scope": c["targetPattern"],
            "status": "PENDING source/target counts, keys, balances and exception file",
            "gate": "Data owner signs reconciliation evidence",
        }
        for c in cards
        if c["type"] == "Table" or "direct_sql" in c["signals"]
    ]
    write(
        suite / "03-data-reconciliation-twin.md",
        "Data Migration Reconciliation Twin",
        "No source/target extracts were supplied; this is a reconciliation contract, not a data-migration result.",
        reconciliation,
        [
            ("Object", "object"),
            ("Target scope", "scope"),
            ("Status", "status"),
            ("Exit gate", "gate"),
        ],
    )
    feature = [
        "Feature: Golden process regression",
        "",
        "  # Generated scenarios require target environment, fixtures, assertions, and execution evidence.",
    ]
    for c in cards:
        feature += [
            "",
            f"  Scenario: {safe_name(c['object'])} approved behavior",
            "    Given approved process data and security role",
            f"    When the D365 target for {c['object']} is executed",
            "    Then the Process Owner accepts the business outcome and exception handling",
        ]
    (suite / "04-golden-process-regression.feature").write_text(
        "\n".join(feature) + "\n", encoding="utf-8"
    )
    proof = {
        "schemaVersion": "1.0",
        "boundary": "This manifest does not compile or deploy X++.",
        "requiredEvidence": [
            "D365 build log",
            "best-practice results",
            "automated test result",
            "target metadata/extension seam",
        ],
        "candidates": [
            {"object": c["object"], "pattern": c["targetPattern"], "status": "UNPROVEN"}
            for c in cards
            if c["decision"] in {"EXTEND", "REBUILD"}
        ],
    }
    (suite / "05-extension-proof-manifest.json").write_text(
        json.dumps(proof, indent=2), encoding="utf-8"
    )
    sentinel = {
        "schemaVersion": "1.0",
        "boundary": "Alert configuration template only; connect approved telemetry separately.",
        "alerts": [
            {
                "name": "Integration failure",
                "trigger": "aif_or_service or direct_sql replacement error",
                "owner": "UNASSIGNED",
                "action": "Open incident, reconcile, evaluate rollback",
            },
            {
                "name": "Security access denial",
                "trigger": "role/privilege failure",
                "owner": "UNASSIGNED",
                "action": "Review role design and test evidence",
            },
            {
                "name": "Process adoption drop",
                "trigger": "approved KPI below baseline",
                "owner": "UNASSIGNED",
                "action": "Run adoption review",
            },
        ],
    }
    (suite / "06-hypercare-sentinel.json").write_text(
        json.dumps(sentinel, indent=2), encoding="utf-8"
    )
    variants = Counter(" + ".join(sorted(c["signals"])) or c["type"] for c in cards)
    write(
        suite / "07-process-variant-elimination.md",
        "Process Variant Elimination Engine",
        "Static clusters are technical variation candidates; confirm frequency and business validity from runtime/process evidence.",
        [
            {
                "variant": k,
                "objects": v,
                "action": "Validate standardization or justified exception",
            }
            for k, v in variants.most_common()
        ],
        [
            ("Variant candidate", "variant"),
            ("Objects", "objects"),
            ("Next action", "action"),
        ],
    )
    audit = [
        {
            "object": c["object"],
            "control": "Decision, owner, target fit, security/data/test evidence",
            "evidence": "; ".join(c["evidence"]),
            "status": "INCOMPLETE until reviewer evidence supplied",
        }
        for c in cards
    ]
    write(
        suite / "08-regulatory-audit-evidence-pack.md",
        "Regulatory & Audit Evidence Pack",
        "Traceability template; it is not an audit opinion or compliance certification.",
        audit,
        [
            ("Object", "object"),
            ("Control", "control"),
            ("Source evidence", "evidence"),
            ("Status", "status"),
        ],
    )
    memory = {
        "schemaVersion": "1.0",
        "boundary": "Use only approved, sanitized reviewer decisions; no raw prompts or personal data.",
        "importedFeedback": len(learning),
        "feedback": learning,
        "nextFeedbackTemplate": {
            "objectId": "object id",
            "action": "ACCEPT|REJECT|REQUEST_EVIDENCE",
            "rationale": "approved decision basis",
            "evidence": ["reference"],
        },
    }
    (suite / "09-migration-learning-memory.json").write_text(
        json.dumps(memory, indent=2), encoding="utf-8"
    )
    waves = [
        {
            "wave": "1",
            "rule": "P0/direct-SQL or critical integration",
            "objects": ", ".join(
                c["object"] for c in cards if review_priority(c) == "P0"
            )
            or "none",
        },
        {
            "wave": "2",
            "rule": "Remaining rebuild candidates",
            "objects": ", ".join(
                c["object"]
                for c in cards
                if c["decision"] == "REBUILD" and review_priority(c) != "P0"
            )
            or "none",
        },
        {
            "wave": "3",
            "rule": "Extension/standard candidates after dependencies validated",
            "objects": ", ".join(
                c["object"] for c in cards if c["decision"] != "REBUILD"
            )
            or "none",
        },
    ]
    write(
        suite / "10-multi-wave-portfolio-optimizer.md",
        "Multi-Wave Portfolio Optimizer",
        "Heuristic wave proposal only; capacity, business calendar, runtime dependency and cutover-window evidence are required.",
        waves,
        [("Wave", "wave"), ("Rule", "rule"), ("Objects", "objects")],
    )
    usps = [
        "D365 Metadata & Extensibility Oracle",
        "Runtime Process Mining Connector",
        "Data Migration Reconciliation Twin",
        "Golden-Process Regression Factory",
        "Extension-Point Proof Engine",
        "Autonomous Hypercare Sentinel",
        "Process Variant Elimination Engine",
        "Regulatory & Audit Evidence Pack",
        "Migration Learning Memory",
        "Multi-Wave Portfolio Optimizer",
    ]
    (suite / "innovation-usp-catalog.json").write_text(
        json.dumps(
            {
                "schemaVersion": "1.0",
                "claimBoundary": "These are reviewable, evidence-adapter capabilities; actual target connectivity, telemetry, compilation and test execution require approved external integrations.",
                "usps": usps,
                "imports": {
                    "d365Metadata": bool(args.d365_metadata),
                    "runtimeEvents": len(events),
                    "learningFeedback": len(learning),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "output": str(suite),
                "objectsAnalysed": len(cards),
                "metadataObjects": len(metadata),
                "runtimeEvents": len(events),
                "learningFeedback": len(learning),
            }
        )
    )


if __name__ == "__main__":
    main()
