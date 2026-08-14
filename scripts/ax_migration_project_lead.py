#!/usr/bin/env python3
"""Generate an evidence-led migration project-lead operating pack."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from ax_migration_inventory import discover
from ax_migration_compiler import decision_cards, markdown_table, review_priority


def md(path, title, boundary, rows, columns):
    lines = [f"# {title}", "", boundary, ""]
    lines += (
        markdown_table(rows, columns)
        if rows
        else ["No evidence supplied; record this as an open project evidence gap."]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(
        description="Create a project-lead operating system from AX migration evidence."
    )
    p.add_argument("input", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument(
        "--project-context",
        type=Path,
        help="Optional sanitized JSON: sponsor, dates, workstream owners, capacity, calendar and budget assumptions.",
    )
    a = p.parse_args()
    if not a.input.exists():
        p.error(f"Input does not exist: {a.input}")
    context = {}
    if a.project_context:
        context = json.loads(a.project_context.read_text(encoding="utf-8"))
        if not isinstance(context, dict):
            p.error("project-context must be a JSON object")
    cards = decision_cards(discover(a.input))
    out = a.out / "project-lead-os"
    out.mkdir(parents=True, exist_ok=True)
    priority = lambda c: review_priority(c)
    workstreams = []
    for c in cards:
        signals = set(c["signals"])
        stream = "Functional & Process"
        if c["type"].startswith("Security") or "security" in signals:
            stream = "Security"
        elif signals & {"direct_sql", "aif_or_service", "batch", "cross_company"}:
            stream = "Integration & Data"
        elif c["type"] == "Report":
            stream = "Reporting"
        elif c["decision"] in {"EXTEND", "REBUILD"}:
            stream = "Technical"
        workstreams.append(
            {
                "object": c["object"],
                "workstream": stream,
                "priority": priority(c),
                "decision": c["decision"],
                "effort": c["effort"],
                "owner": "UNASSIGNED",
                "dependency": ", ".join(c["dependencies"]) or "none",
            }
        )
    md(
        out / "01-project-charter.md",
        "Migration Project Charter",
        "Scope, benefits, dates, budget, sponsor and capacity are unverified until supplied in --project-context.",
        [
            {
                "field": "Objective",
                "value": "Migrate approved AX capabilities to supported D365 F&O patterns with traceable decisions and evidence.",
            },
            {"field": "Sponsor", "value": context.get("sponsor", "UNASSIGNED")},
            {
                "field": "Scope basis",
                "value": f"{len(cards)} static AX objects analysed",
            },
            {
                "field": "Success gate",
                "value": "Owner-approved decisions, target validation, test evidence and cutover readiness.",
            },
        ],
        [("Field", "field"), ("Value", "value")],
    )
    md(
        out / "02-work-breakdown-structure.md",
        "Work Breakdown Structure",
        "Effort bands are heuristic planning inputs, not a commitment.",
        workstreams,
        [
            ("Object", "object"),
            ("Workstream", "workstream"),
            ("Priority", "priority"),
            ("Decision", "decision"),
            ("Effort", "effort"),
            ("Owner", "owner"),
        ],
    )
    raid = []
    for c in cards:
        if priority(c) in {"P0", "P1"}:
            raid.append(
                {
                    "id": c["object"],
                    "kind": "RISK",
                    "description": c["rationale"],
                    "impact": f"{c['risk']}/5",
                    "owner": "UNASSIGNED",
                    "response": "Validate evidence, assign mitigation and exit gate.",
                }
            )
    md(
        out / "03-raid-log.md",
        "RAID Log",
        "Generated risks require human ownership and periodic review.",
        raid,
        [
            ("ID", "id"),
            ("Type", "kind"),
            ("Risk/issue", "description"),
            ("Impact", "impact"),
            ("Owner", "owner"),
            ("Response", "response"),
        ],
    )
    roles = [
        {"role": r, "accountable": "UNASSIGNED", "responsibility": d}
        for r, d in [
            ("Executive sponsor", "Outcome, funding and escalations"),
            ("Project lead", "Plan, RAID, governance and decision cadence"),
            ("Process Owner", "Standard-first decisions and UAT acceptance"),
            ("Technical lead", "Target architecture/build evidence"),
            ("Data & integration lead", "Contracts, reconciliation and cutover"),
            ("Security lead", "Access and SoD evidence"),
        ]
    ]
    md(
        out / "04-raci.md",
        "RACI & Ownership",
        "Named people are required before this becomes an operating RACI.",
        roles,
        [
            ("Role", "role"),
            ("Accountable", "accountable"),
            ("Responsibility", "responsibility"),
        ],
    )
    waves = [
        {
            "wave": "1",
            "exit": "P0 risks have owners, mitigation, target fit and rollback evidence",
            "objects": ", ".join(c["object"] for c in cards if priority(c) == "P0")
            or "none",
        },
        {
            "wave": "2",
            "exit": "Rebuild candidates have approved architecture and integration/data contracts",
            "objects": ", ".join(
                c["object"]
                for c in cards
                if c["decision"] == "REBUILD" and priority(c) != "P0"
            )
            or "none",
        },
        {
            "wave": "3",
            "exit": "Extensions/configuration pass build, test and process acceptance",
            "objects": ", ".join(
                c["object"] for c in cards if c["decision"] != "REBUILD"
            )
            or "none",
        },
    ]
    md(
        out / "05-integrated-wave-plan.md",
        "Integrated Wave Plan",
        "No dates are predicted without calendar, capacity, dependency and environment evidence.",
        waves,
        [("Wave", "wave"), ("Exit gate", "exit"), ("Objects", "objects")],
    )
    changes = {
        "schemaVersion": "1.0",
        "policy": "No scope, timeline, budget or architecture change is approved automatically.",
        "requests": [
            {
                "id": "CR-001",
                "title": "Describe change",
                "impact": "scope/schedule/cost/risk/test/data",
                "options": ["ACCEPT", "REJECT", "DEFER"],
                "decisionOwner": "UNASSIGNED",
                "evidence": [],
            }
        ],
    }
    (out / "06-change-control-template.json").write_text(
        json.dumps(changes, indent=2), encoding="utf-8"
    )
    governance = [
        {
            "forum": "Daily workstream",
            "purpose": "Blockers, dependencies, next evidence",
            "decision": "No commitment without owner",
        },
        {
            "forum": "Weekly programme",
            "purpose": "RAID, wave gates, scope",
            "decision": "Escalate P0/P1",
        },
        {
            "forum": "Design authority",
            "purpose": "Standard/configure/extend/rebuild/retire",
            "decision": "Process Owner records outcome",
        },
        {
            "forum": "Steering committee",
            "purpose": "Investment, risk acceptance, major scope",
            "decision": "Sponsor decision recorded",
        },
    ]
    md(
        out / "07-governance-cadence.md",
        "Governance & Decision Cadence",
        "Meeting cadence is a template; organizations must assign attendees and dates.",
        governance,
        [("Forum", "forum"), ("Purpose", "purpose"), ("Decision rule", "decision")],
    )
    status = [
        {
            "area": "Scope",
            "status": (
                "AMBER" if any(c["decision"] == "REBUILD" for c in cards) else "GREEN"
            ),
            "evidence": "Decision inventory",
        },
        {
            "area": "Risk",
            "status": "RED" if any(priority(c) == "P0" for c in cards) else "AMBER",
            "evidence": "RAID candidates",
        },
        {
            "area": "Schedule",
            "status": "UNASSESSED",
            "evidence": "No capacity/calendar supplied",
        },
        {
            "area": "Budget",
            "status": "UNASSESSED",
            "evidence": "No rate card/baseline supplied",
        },
        {
            "area": "Quality",
            "status": "AMBER",
            "evidence": "Test skeletons require execution",
        },
    ]
    md(
        out / "08-weekly-status-report.md",
        "Weekly Status Report",
        "RAG is evidence-labelled; it is not a management approval.",
        status,
        [("Area", "area"), ("Status", "status"), ("Evidence", "evidence")],
    )
    cutover = [
        {
            "gate": "Business/process acceptance",
            "owner": "UNASSIGNED",
            "evidence": "Approved UAT result",
        },
        {
            "gate": "Data reconciliation",
            "owner": "UNASSIGNED",
            "evidence": "Source/target counts, balances and exception sign-off",
        },
        {
            "gate": "Integration & security",
            "owner": "UNASSIGNED",
            "evidence": "Contract/access test results",
        },
        {
            "gate": "Rollback & hypercare",
            "owner": "UNASSIGNED",
            "evidence": "Rehearsed fallback and incident roster",
        },
    ]
    md(
        out / "09-cutover-command-center.md",
        "Cutover Command Center",
        "No artifact certifies cutover safety; all gates require executed evidence and accountable approval.",
        cutover,
        [("Gate", "gate"), ("Owner", "owner"), ("Evidence", "evidence")],
    )
    operating = {
        "schemaVersion": "1.0",
        "autonomousActions": [
            "Refresh static inventory",
            "Prepare RAID and status drafts",
            "Prioritize unowned P0/P1 decisions",
            "Generate meeting briefs and decision templates",
        ],
        "humanOnly": [
            "People management",
            "Budget/contract commitments",
            "Formal risk acceptance",
            "Production deployment/go-live approval",
            "External communications",
        ],
        "contextImported": bool(context),
    }
    (out / "10-project-lead-operating-contract.json").write_text(
        json.dumps(operating, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(out),
                "objectsAnalysed": len(cards),
                "p0": sum(priority(c) == "P0" for c in cards),
                "contextImported": bool(context),
            }
        )
    )


if __name__ == "__main__":
    main()
