#!/usr/bin/env python3
"""Create review-gated Azure DevOps sync payloads from AX migration evidence.

This script never stores credentials and never calls Azure DevOps. A Codex session with
an approved Azure DevOps connector may execute reviewed payloads using its available tools.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from ax_migration_inventory import discover
from ax_migration_compiler import decision_cards, review_priority


def main():
    p = argparse.ArgumentParser(
        description="Create Azure DevOps Boards/Repos sync payloads."
    )
    p.add_argument("input", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--organization", help="Azure DevOps organization name; optional")
    p.add_argument("--project", help="Azure DevOps project name; optional")
    a = p.parse_args()
    if not a.input.exists():
        p.error(f"Input does not exist: {a.input}")
    cards = decision_cards(discover(a.input))
    out = a.out / "azure-devops"
    out.mkdir(parents=True, exist_ok=True)
    workstreams = {
        "Integration & Data": [],
        "Security": [],
        "Reporting": [],
        "Technical": [],
        "Process & Functional": [],
    }
    for c in cards:
        s = set(c["signals"])
        ws = "Process & Functional"
        if c["type"].startswith("Security") or "security" in s:
            ws = "Security"
        elif s & {"direct_sql", "aif_or_service", "batch", "cross_company"}:
            ws = "Integration & Data"
        elif c["type"] == "Report":
            ws = "Reporting"
        elif c["decision"] in {"EXTEND", "REBUILD"}:
            ws = "Technical"
        workstreams[ws].append(c)
    items = [
        {
            "clientKey": "EPIC-MIGRATION",
            "workItemType": "Epic",
            "title": "AX 2012 to D365 F&O migration",
            "state": "Proposed",
            "approved": False,
            "tags": ["migration", "generated"],
            "description": "Generated program container. Requires sponsor approval before creation.",
        }
    ]
    for name, group in workstreams.items():
        if not group:
            continue
        key = "FEATURE-" + name.upper().replace(" ", "-").replace("&", "AND")
        items.append(
            {
                "clientKey": key,
                "parent": "EPIC-MIGRATION",
                "workItemType": "Feature",
                "title": name,
                "state": "Proposed",
                "approved": False,
                "tags": ["migration", "generated"],
                "description": "Generated workstream; assign a named owner before synchronization.",
            }
        )
        for c in group:
            items.append(
                {
                    "clientKey": f"OBJ-{c['objectId']}",
                    "parent": key,
                    "workItemType": "Product Backlog Item",
                    "title": f"{c['decision']}: {c['object']}",
                    "state": "New",
                    "approved": False,
                    "priority": review_priority(c),
                    "effort": c["effort"],
                    "tags": ["ax-migration", c["type"], c["decision"].lower()],
                    "description": c["rationale"],
                    "acceptanceCriteria": [
                        "Business owner confirms usage",
                        "D365 target fit/extension seam validated",
                        "Test and security/data evidence attached",
                    ],
                    "evidence": c["evidence"],
                }
            )
    plan = {
        "schemaVersion": "1.0",
        "organization": a.organization or "UNASSIGNED",
        "project": a.project or "UNASSIGNED",
        "mode": "REVIEW_ONLY",
        "connectorRequirement": "Use an authenticated Azure DevOps Codex connector with explicit create/update permissions.",
        "safety": {
            "neverAutoMerge": True,
            "neverAutoDeploy": True,
            "neverStoreCredentials": True,
            "requiresApprovalBeforeWrite": True,
        },
        "workItems": items,
    }
    (out / "boards-sync-payload.json").write_text(
        json.dumps(plan, indent=2), encoding="utf-8"
    )
    prs = {
        "schemaVersion": "1.0",
        "mode": "REVIEW_ONLY",
        "pullRequests": [
            {
                "title": f"D365 migration proposal: {c['object']}",
                "branch": "migration/" + c["object"].lower(),
                "approved": False,
                "requiredChecks": [
                    "D365 build",
                    "Best practice",
                    "Automated tests",
                    "Architecture review",
                ],
                "evidence": c["evidence"],
            }
            for c in cards
            if c["decision"] in {"EXTEND", "REBUILD"}
        ],
        "policy": "Create a PR only after a generated proposal is placed in a target repo and a human author approves the payload. Never merge automatically.",
    }
    (out / "pull-request-payload.json").write_text(
        json.dumps(prs, indent=2), encoding="utf-8"
    )
    build = {
        "schemaVersion": "1.0",
        "mode": "READ_ONLY_EVIDENCE",
        "requiredBuildEvidence": [
            "pipeline run URL/id",
            "commit SHA",
            "build result",
            "best-practice results",
            "test result summary",
            "artifact version",
        ],
        "mapping": [
            {
                "object": c["object"],
                "workItemClientKey": f"OBJ-{c['objectId']}",
                "status": "AWAITING_PIPELINE_EVIDENCE",
            }
            for c in cards
        ],
    }
    (out / "build-test-evidence-template.json").write_text(
        json.dumps(build, indent=2), encoding="utf-8"
    )
    guide = [
        "# Azure DevOps adapter",
        "",
        "1. In Codex, authenticate the Azure DevOps connector and select organization/project.",
        "2. Review `boards-sync-payload.json`; replace `UNASSIGNED`, assign owners, and mark only approved records for creation.",
        "3. Use available Azure Boards write tools to create/update reviewed work items. If no write tool is exposed, keep the payload as the handoff artifact.",
        "4. Create reviewed PRs only; preserve branch policy and never auto-merge/deploy.",
        "5. Import pipeline/build/test evidence into the matching work item and migration review queue.",
        "",
        "The adapter itself has no Azure credentials and performs no external write.",
    ]
    (out / "README.md").write_text("\n".join(guide) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "output": str(out),
                "workItems": len(items),
                "pullRequests": len(prs["pullRequests"]),
                "mode": "REVIEW_ONLY",
            }
        )
    )


if __name__ == "__main__":
    main()
