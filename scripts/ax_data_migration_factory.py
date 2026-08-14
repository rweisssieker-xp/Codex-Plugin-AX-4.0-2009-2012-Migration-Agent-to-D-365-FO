#!/usr/bin/env python3
"""Generate review-gated AX→D365 data-migration factory artifacts; never moves data."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from ax_migration_inventory import discover
from ax_migration_compiler import decision_cards, markdown_table


def md(p, t, b, r, c):
    l = [f"# {t}", "", b, ""]
    l += (
        markdown_table(r, c)
        if r
        else ["No evidence supplied; this is an open migration gap."]
    )
    p.write_text("\n".join(l) + "\n", encoding="utf-8")


def main():
    p = argparse.ArgumentParser(
        description="Create data migration mapping, load and reconciliation artifacts."
    )
    p.add_argument("input", type=Path)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument(
        "--target-entities",
        type=Path,
        help="Sanitized JSON list of D365 data entities/fields",
    )
    p.add_argument(
        "--profile", type=Path, help="Sanitized JSON source profiling results"
    )
    a = p.parse_args()
    if not a.input.exists():
        p.error(f"Input does not exist: {a.input}")
    load = lambda x: json.loads(x.read_text(encoding="utf-8")) if x else []
    entities = load(a.target_entities)
    profile = load(a.profile)
    cards = decision_cards(discover(a.input))
    tables = [
        c
        for c in cards
        if c["type"] in {"Table", "EDT", "Enum"} or "direct_sql" in c["signals"]
    ]
    o = a.out / "data-migration-factory"
    o.mkdir(parents=True, exist_ok=True)
    meta = (
        entities
        if isinstance(entities, list)
        else entities.get("entities", []) if isinstance(entities, dict) else []
    )
    names = {str(x.get("name", "")).lower() for x in meta if isinstance(x, dict)}
    mapping = [
        {
            "source": c["object"],
            "sourceType": c["type"],
            "targetEntity": (
                c["object"] + "Entity"
                if (c["object"] + "entity").lower() in names
                else "UNMAPPED"
            ),
            "status": "REVIEW_REQUIRED",
            "rule": "Map key, company, lookup, enum, default, date and retention explicitly",
        }
        for c in tables
    ]
    md(
        o / "01-source-target-mapping.md",
        "Source-to-Target Mapping Workbench",
        "Field-level source metadata is required; no target entity is invented.",
        mapping,
        [
            ("Source", "source"),
            ("Type", "sourceType"),
            ("Target", "targetEntity"),
            ("Status", "status"),
            ("Rule", "rule"),
        ],
    )
    md(
        o / "02-data-profiling.md",
        "Data Profiling",
        "Uses only supplied sanitized profiling output; never reads production data directly.",
        profile if isinstance(profile, list) else [],
        [
            ("table", "table"),
            ("metric", "metric"),
            ("value", "value"),
            ("finding", "finding"),
        ],
    )
    transformations = {
        "schemaVersion": "1.0",
        "mode": "REVIEW_ONLY",
        "rules": [
            {
                "source": x["source"],
                "rules": [
                    "key/lookup mapping",
                    "legal entity mapping",
                    "enum translation",
                    "date/time normalization",
                    "default/mandatory handling",
                    "retention/PII decision",
                ],
                "approved": False,
            }
            for x in mapping
        ],
    }
    (o / "03-transformation-rules.json").write_text(
        json.dumps(transformations, indent=2), encoding="utf-8"
    )
    sequence = [
        {
            "order": 1,
            "group": "Reference/master data",
            "gate": "keys and lookups resolved",
        },
        {
            "order": 2,
            "group": "Transactional/open items",
            "gate": "master/reference reconciliation passed",
        },
        {
            "order": 3,
            "group": "History/archive",
            "gate": "retention and business-access decision approved",
        },
    ]
    md(
        o / "04-load-sequence.md",
        "Load Sequencing",
        "Actual dependency ordering requires field relations and target entity metadata.",
        sequence,
        [("Order", "order"), ("Group", "group"), ("Gate", "gate")],
    )
    staging = {
        "schemaVersion": "1.0",
        "mode": "NO_EXECUTION",
        "stages": [
            "extract",
            "profile",
            "transform",
            "validate",
            "package",
            "import",
            "reconcile",
        ],
        "retryPolicy": {
            "maxAttempts": "SET_BY_OWNER",
            "quarantine": "exception queue",
            "resume": "idempotent batch key",
        },
        "approvalRequired": True,
    }
    (o / "05-staging-retry-exception.json").write_text(
        json.dumps(staging, indent=2), encoding="utf-8"
    )
    rec = [
        {
            "object": x["source"],
            "checks": "count, key uniqueness, referential integrity, balance/hash where applicable",
            "status": "PENDING source and target extracts",
            "owner": "UNASSIGNED",
        }
        for x in mapping
    ]
    md(
        o / "06-reconciliation-engine.md",
        "Reconciliation Engine",
        "No counts, balances, hashes or target extracts were supplied; no reconciliation result is claimed.",
        rec,
        [
            ("Object", "object"),
            ("Checks", "checks"),
            ("Status", "status"),
            ("Owner", "owner"),
        ],
    )
    compliance = [
        {
            "object": x["source"],
            "decision": "Classify PII, retention, legal hold and archive requirement",
            "status": "UNASSESSED",
            "owner": "Data Owner",
        }
        for x in mapping
    ]
    md(
        o / "07-privacy-retention.md",
        "Privacy, Retention & Archive",
        "No personal data classification is inferred from object names.",
        compliance,
        [
            ("Object", "object"),
            ("Decision", "decision"),
            ("Status", "status"),
            ("Owner", "owner"),
        ],
    )
    uat = [
        {
            "scenario": f'Data migration acceptance: {x["source"]}',
            "given": "approved mapping and fixture",
            "when": "package is imported and reconciled",
            "then": "Data Owner accepts exceptions and business balance",
        }
        for x in mapping
    ]
    md(
        o / "08-data-uat.md",
        "Data Migration UAT",
        "Generated scenarios require execution in an approved non-production environment.",
        uat,
        [
            ("Scenario", "scenario"),
            ("Given", "given"),
            ("When", "when"),
            ("Then", "then"),
        ],
    )
    payload = {
        "schemaVersion": "1.0",
        "mode": "REVIEW_ONLY",
        "connector": "D365 Data Management/OData/package API requires approved external adapter",
        "entities": [
            {
                "source": x["source"],
                "target": x["targetEntity"],
                "action": "IMPORT_AFTER_APPROVAL",
                "package": "UNASSIGNED",
                "approved": False,
            }
            for x in mapping
        ],
        "safety": [
            "no credentials",
            "no production write",
            "backup/rollback required",
            "Data Owner sign-off required",
        ],
    }
    (o / "09-d365-import-payload.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    cut = [
        {"gate": "Mapping and transformation approval", "owner": "Data Owner"},
        {"gate": "Profile/data-quality threshold", "owner": "Data Lead"},
        {
            "gate": "Reconciliation pass and exception sign-off",
            "owner": "Business Owner",
        },
        {
            "gate": "Backup, rollback and import authorization",
            "owner": "Cutover Manager",
        },
    ]
    md(
        o / "10-data-cutover-gates.md",
        "Data Cutover Gates",
        "No import is authorized by this artifact.",
        cut,
        [("Gate", "gate"), ("Owner", "owner")],
    )
    print(
        json.dumps(
            {
                "output": str(o),
                "mappingCandidates": len(mapping),
                "targetEntities": len(meta),
                "mode": "REVIEW_ONLY",
            }
        )
    )


if __name__ == "__main__":
    main()
