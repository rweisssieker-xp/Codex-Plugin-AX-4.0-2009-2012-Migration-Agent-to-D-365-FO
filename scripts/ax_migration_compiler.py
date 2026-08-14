#!/usr/bin/env python3
"""Evidence-led AX to D365 F&O decision compiler.

Small, composable writers keep portfolio, review, proposal and stakeholder output
maintainable. All target assertions require human validation.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from ax_migration_inventory import discover, sha256


def effort(risk, signals):
    if risk >= 4 or "direct_sql" in signals:
        return "L (8–20 days; validate integration/data redesign first)"
    if risk == 3:
        return "M (3–8 days; validate target architecture)"
    if risk == 2:
        return "S (1–3 days; confirm standard fit and extension seam)"
    return "XS (≤1 day; validate removal/standard configuration decision)"


def target_pattern(row):
    signals, kind = set(row["signals"]), row["type"]
    rules = [
        (
            kind.startswith("Security"),
            "D365 security role/duty/privilege redesign",
            "REBUILD",
            "Map personas and segregation-of-duties; do not port role names mechanically.",
        ),
        (
            "direct_sql" in signals,
            "D365 data entity, service, query, or business event",
            "REBUILD",
            "Replace database access with a supported pattern after data ownership review.",
        ),
        (
            "aif_or_service" in signals,
            "Custom service, OData/data entity, or business event",
            "REBUILD",
            "Choose contract, error handling and ownership with the integration lead.",
        ),
        (
            "ssrs_or_morphx_report" in signals or kind == "Report",
            "SSRS report extension or new SSRS report design",
            "REBUILD",
            "Validate decision purpose, print management and distribution.",
        ),
        (
            "client_or_legacy_api" in signals,
            "Server-safe service or supported platform API",
            "REBUILD",
            "Remove client, COM and CLR assumptions; define security boundaries.",
        ),
        (
            kind == "Table",
            "Table extension and data entity extension",
            "EXTEND",
            "Check standard ownership and entity availability before adding fields.",
        ),
        (
            kind in {"Form", "MenuItem"},
            "Form extension plus supported menu item",
            "EXTEND",
            "Prefer controls and handlers over replacement forms.",
        ),
        (
            kind in {"Class", "Service", "DataEntity"},
            "Event handler, delegate, or Chain of Command",
            "EXTEND",
            "Use only a documented extension point; otherwise record redesign.",
        ),
        (
            kind in {"EDT", "Enum", "Query", "View", "Map"},
            "Metadata extension or D365 standard configuration",
            "EXTEND",
            "Confirm target artifact and supported extension semantics.",
        ),
    ]
    for applies, target, decision, reason in rules:
        if applies:
            return target, decision, reason
    return (
        "D365 standard configuration assessment",
        "STANDARD",
        "Confirm standard fit with the Process Owner and target documentation.",
    )


def decision_cards(records):
    cards = []
    for row in records:
        target, recommended, rationale = target_pattern(row)
        decision = (
            row["classification"] if row["classification"] == "REBUILD" else recommended
        )
        cards.append(
            {
                "objectId": row["id"],
                "object": row["name"],
                "type": row["type"],
                "decision": decision,
                "heuristicDecision": row["classification"],
                "confidence": "low",
                "risk": row["risk"],
                "effort": effort(row["risk"], row["signals"]),
                "targetPattern": target,
                "rationale": rationale,
                "signals": row["signals"],
                "dependencies": row["dependencies"],
                "evidence": row["evidence"],
                "decisionRequired": [
                    "Confirm business owner and actual usage.",
                    "Validate target D365 version, modules and extensibility seam.",
                ],
                "testEvidence": [
                    "Unit/SysTest",
                    "Integration/API contract",
                    "Security/access",
                    "Data migration/regression",
                ],
            }
        )
    return cards


def markdown_table(rows, columns):
    result = [
        "| " + " | ".join(label for label, _ in columns) + " |",
        "|" + "|".join("---" for _ in columns) + "|",
    ]
    for row in rows:
        result.append(
            "| "
            + " | ".join(
                str(row.get(key, "—")).replace("|", "\\|") for _, key in columns
            )
            + " |"
        )
    return result


def safe_name(value):
    return re.sub(r"[^A-Za-z0-9_]", "_", value)[:80] or "AxObject"


def review_priority(card):
    if card["risk"] >= 4 or "direct_sql" in card["signals"]:
        return "P0"
    return "P1" if card["risk"] >= 3 or card["decision"] == "REBUILD" else "P2"


def counter_hypothesis(card):
    if "direct_sql" in card["signals"]:
        return "This may be a dormant staging path; prove business usage and external consumers before rebuilding."
    if card["type"].startswith("Security"):
        return "A standard role and configuration may meet the persona need; prove the SoD gap first."
    return "D365 configuration or a standard process may meet the retained requirement; prove the customization need."


def write_json(path, payload):
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_markdown(path, title, boundary, rows, columns):
    lines = [f"# {title}", "", boundary, ""]
    lines.extend(
        markdown_table(rows, columns)
        if rows
        else [
            "No matching evidence was found. Record this as an evidence gap, not an absence claim."
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_core_outputs(out, records, cards):
    counts = Counter(card["decision"] for card in cards)
    write_json(out / "inventory.json", {"schemaVersion": "1.1", "objects": records})
    write_json(
        out / "decision-compiler.json",
        {
            "schemaVersion": "1.0",
            "summary": {"objectsAnalysed": len(cards), "decisions": counts},
            "decisions": cards,
        },
    )
    rows = [
        {
            "object": c["object"],
            "type": c["type"],
            "decision": c["decision"],
            "risk": f"{c['risk']}/5",
            "target": c["targetPattern"],
            "effort": c["effort"],
        }
        for c in cards
    ]
    title = f"AX 2012 → D365 F&O migration backlog ({len(cards):,} objects analysed; {counts['STANDARD']:,} standard; {counts['REMOVE']:,} remove; {counts['EXTEND']:,} extend; {counts['REBUILD']:,} rebuild)"
    write_markdown(
        out / "migration-backlog.md",
        title,
        "All classifications are reviewable hypotheses.",
        rows,
        [
            ("Object", "object"),
            ("Type", "type"),
            ("Decision", "decision"),
            ("Risk", "risk"),
            ("Target", "target"),
            ("Effort", "effort"),
        ],
    )
    write_markdown(
        out / "d365-standard-fit.md",
        "D365 Standard-Fit Navigator",
        "Validate version, module, licence and configuration before retaining custom code.",
        rows,
        [
            ("Object", "object"),
            ("Decision", "decision"),
            ("Target hypothesis", "target"),
            ("Risk", "risk"),
        ],
    )
    nonstandard = [row for row in rows if row["decision"] != "STANDARD"]
    write_markdown(
        out / "extension-coach.md",
        "Overlayering-to-Extension Refactoring Coach",
        "Prefer configuration, metadata extension, event/delegate handler, then CoC at a verified seam.",
        nonstandard,
        [
            ("Object", "object"),
            ("Decision", "decision"),
            ("Target", "target"),
            ("Risk", "risk"),
        ],
    )
    test_rows = [
        {
            "object": c["object"],
            "decision": c["decision"],
            "coverage": "; ".join(c["testEvidence"]),
            "gate": "Executed target evidence and owner acceptance",
        }
        for c in cards
    ]
    write_markdown(
        out / "test-strategy.md",
        "Migration Test Evidence Factory",
        "Generated scope is a test design, never proof that a test ran.",
        test_rows,
        [
            ("Object", "object"),
            ("Decision", "decision"),
            ("Coverage", "coverage"),
            ("Acceptance", "gate"),
        ],
    )


def write_proposals(out, cards):
    proposed = out / "proposed"
    proposed.mkdir(exist_ok=True)
    index = []
    for card in cards:
        if card["decision"] not in {"EXTEND", "REBUILD"}:
            continue
        name = safe_name(card["object"])
        design = proposed / f"{name}_MigrationDesign.md"
        design.write_text(
            f"# {card['object']} migration design\n\nDecision: {card['decision']}\n\nTarget pattern: {card['targetPattern']}\n\nValidate metadata, compile, security, test and Process Owner acceptance before release.\n",
            encoding="utf-8",
        )
        test = proposed / f"{name}_MigrationTests.xpp"
        test.write_text(
            f"class {name}_MigrationTests extends SysTestCase\n{{\n    [SysTestMethod]\n    public void test_ApprovedTargetBehavior()\n    {{\n        this.assertTrue(true, 'Replace with approved assertion for {card['object']}.');\n    }}\n}}\n",
            encoding="utf-8",
        )
        index.append(
            {
                "object": card["object"],
                "design": design.name,
                "test": test.name,
                "status": "REVIEW_ONLY",
            }
        )
    write_json(
        proposed / "proposal-index.json",
        {
            "boundary": "No generated proposal is compiled or deployable evidence.",
            "items": index,
        },
    )


def write_review_room(out, cards):
    room = out / "review-room"
    room.mkdir(exist_ok=True)
    queue = [
        {
            "reviewId": f"review:{c['objectId']}",
            "priority": review_priority(c),
            "status": "NEEDS_REVIEW",
            "owner": "UNASSIGNED",
            "object": c["object"],
            "decision": c["decision"],
            "targetPattern": c["targetPattern"],
            "counterHypothesis": counter_hypothesis(c),
            "requiredEvidence": [
                "Business owner and usage",
                "D365 fit and extension seam",
                "Test/security/data acceptance",
            ],
            "allowedActions": [
                "ACCEPT",
                "REJECT",
                "REQUEST_EVIDENCE",
                "DEFER",
                "REMOVE_CANDIDATE",
            ],
        }
        for c in sorted(
            cards,
            key=lambda item: (
                {"P0": 0, "P1": 1, "P2": 2}[review_priority(item)],
                -item["risk"],
            ),
        )
    ]
    write_json(
        room / "migration-review-queue.json", {"schemaVersion": "1.0", "items": queue}
    )
    write_json(
        room / "decision-update-template.json",
        {
            "schemaVersion": "1.0",
            "updates": [
                {
                    "reviewId": "review:objectId",
                    "action": "ACCEPT|REJECT|REQUEST_EVIDENCE|DEFER|REMOVE_CANDIDATE",
                    "actor": "name/team",
                    "rationale": "decision basis",
                    "evidenceAdded": ["approved reference"],
                }
            ],
        },
    )


SUITES = {
    "usp-suite": [
        ("Evidence-to-Decision Compiler", "Migration architect"),
        ("Standard-Fit Falsifier", "Functional architect"),
        ("Overlayering Excavator", "Technical architect"),
        ("X++ Intent Reconstruction", "Business analyst"),
        ("Integration Contract Autopsy", "Integration architect"),
        ("Data Semantic Successor", "Data migration lead"),
        ("Security Delta Navigator", "Security architect"),
        ("Report-to-Decision Transformer", "Reporting lead"),
        ("Cutover Failure Simulator", "Cutover manager"),
        ("ISV Exit Intelligence", "Vendor manager"),
    ],
    "executive-suite": [
        ("Portfolio Risk & Investment Engine", "CIO/CFO"),
        ("Scope Volatility Forecaster", "Programme lead"),
        ("Standardization Value Ledger", "CFO"),
        ("Benefit Realization Contract", "Executive sponsor"),
        ("Executive Decision Briefing Agent", "Steering committee"),
        ("Migration Black-Swan Radar", "Risk officer"),
        ("Vendor & ISV Negotiation Intelligence", "Procurement"),
        ("Cutover Air-Traffic Control", "COO"),
        ("Architecture Debt Balance Sheet", "Enterprise architect"),
        ("Board-Ready Migration Narrative", "CEO/Board"),
    ],
    "process-suite": [
        ("Process-to-Standard Twin", "Process Owner"),
        ("Fit-to-Standard Challenger", "Process Owner"),
        ("Exception Mining Agent", "Process Manager"),
        ("Configuration-First Planner", "Functional lead"),
        ("Process Retirement Detector", "Process Owner"),
        ("Standard Adoption Coach", "Change lead"),
        ("UAT Scenario Compiler", "Process Owner"),
        ("Process KPI Contract", "Process Manager"),
        ("Cross-Process Impact Navigator", "Process Owner"),
        ("Autonomous Design Authority Queue", "Design Authority"),
    ],
}


def write_suite(out, folder, cards):
    suite = out / folder
    suite.mkdir(exist_ok=True)
    catalog = []
    exposure = [
        {
            "object": c["object"],
            "decision": c["decision"],
            "risk": f"{c['risk']}/5",
            "evidence": "; ".join(c["evidence"]),
        }
        for c in cards
        if review_priority(c) in {"P0", "P1"}
    ]
    for number, (title, audience) in enumerate(SUITES[folder], 1):
        item = {
            "id": number,
            "title": title,
            "audience": audience,
            "mode": "REVIEW_GATED",
            "metric": "Owner-approved evidence-complete decisions",
            "killCondition": "Stop or revise if five qualified reviews do not reduce cycle time or rework.",
            "rollback": "Discard generated view; retain source inventory and decision log.",
        }
        catalog.append(item)
        write_markdown(
            suite / f"{number:02d}-{safe_name(title).lower()}.md",
            title,
            f"Audience: {audience}. Static AX evidence is not proof of target capability, runtime usage or approval.",
            exposure,
            [
                ("Object", "object"),
                ("Decision", "decision"),
                ("Risk", "risk"),
                ("Evidence", "evidence"),
            ],
        )
    write_json(
        suite / "catalog.json", {"schemaVersion": "1.0", "capabilities": catalog}
    )


def write_manifest(out, input_path):
    files = (
        [input_path]
        if input_path.is_file()
        else [path for path in input_path.rglob("*") if path.is_file()]
    )
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "tool": "ax_migration_compiler.py",
        "inputs": [
            {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in files
        ],
        "limitations": [
            "Static analysis only; no runtime telemetry, metadata lookup, compilation or test execution.",
            "All decisions require reviewer approval.",
        ],
    }
    write_json(out / "input-manifest.json", payload)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Compile AX migration decisions and review-gated deliverables."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--generate-proposals", action="store_true")
    parser.add_argument("--review-room", action="store_true")
    parser.add_argument("--usp-suite", action="store_true")
    parser.add_argument("--executive-suite", action="store_true")
    parser.add_argument("--process-suite", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"Input does not exist: {args.input}")
    args.out.mkdir(parents=True, exist_ok=True)
    records = discover(args.input)
    cards = decision_cards(records)
    write_manifest(args.out, args.input)
    write_core_outputs(args.out, records, cards)
    if args.generate_proposals:
        write_proposals(args.out, cards)
    if args.review_room:
        write_review_room(args.out, cards)
    for enabled, folder in [
        (args.usp_suite, "usp-suite"),
        (args.executive_suite, "executive-suite"),
        (args.process_suite, "process-suite"),
    ]:
        if enabled:
            write_suite(args.out, folder, cards)
    print(
        json.dumps(
            {
                "output": str(args.out),
                "objectsAnalysed": len(cards),
                "decisions": Counter(card["decision"] for card in cards),
            }
        )
    )


if __name__ == "__main__":
    main()
