#!/usr/bin/env python3
"""Validate evidence, create reproducible delivery controls and management views."""
from __future__ import annotations

import argparse
from pathlib import Path

from ax_migration_support import (
    read_json,
    run_manifest,
    scan_path,
    timestamp,
    write_json,
)


SCHEMA_KEYS = {
    "d365-metadata": ("objects", "d365-metadata.schema.json"),
    "runtime-events": ("events", "runtime-events.schema.json"),
    "build-evidence": ("builds", "build-evidence.schema.json"),
    "isv-register": ("vendors", "isv-register.schema.json"),
    "data-profile": ("tables", "data-profile.schema.json"),
}


def validate_payload(label, path, schema_root):
    findings = scan_path(path)
    result = {
        "input": label,
        "path": str(path),
        "status": "VALID",
        "findings": findings,
    }
    if findings:
        result["status"] = "BLOCKED_SENSITIVE_CONTENT"
        return result
    try:
        data = read_json(path)
    except Exception as error:
        return {
            **result,
            "status": "INVALID_JSON",
            "findings": [{"category": "json", "action": str(error)}],
        }
    key, schema = SCHEMA_KEYS[label]
    if not isinstance(data, dict) or not isinstance(data.get(key), list):
        return {
            **result,
            "status": "SCHEMA_GAP",
            "findings": [
                {
                    "category": "schema",
                    "action": f"Expected array '{key}' defined in {schema}.",
                }
            ],
        }
    result["schema"] = str(schema_root / schema)
    result["records"] = len(data[key])
    return result


def load_decisions(path):
    data = read_json(path)
    return data.get("decisions", []) if isinstance(data, dict) else []


def evidence_ledger(cards, manifest):
    entries = []
    for card in cards:
        entries.append(
            {
                "objectId": card["objectId"],
                "object": card["object"],
                "sourceEvidence": card["evidence"],
                "decision": card["decision"],
                "requiredClosure": [
                    "Owner decision",
                    "Target metadata",
                    "Build/BP",
                    "Executed test",
                    "Deployment approval",
                ],
                "runId": manifest["runId"],
                "status": "OPEN",
            }
        )
    return {"schemaVersion": "1.0", "generatedAt": timestamp(), "entries": entries}


def dashboard(cards, validations, language):
    decisions = {}
    for card in cards:
        decisions[card["decision"]] = decisions.get(card["decision"], 0) + 1
    return {
        "schemaVersion": "1.0",
        "mode": "EVIDENCE_LABELLED",
        "language": language,
        "kpis": {
            "objectsAnalysed": len(cards),
            "decisions": decisions,
            "p0": sum(card["risk"] >= 4 for card in cards),
            "unvalidatedInputs": sum(item["status"] != "VALID" for item in validations),
        },
        "decisionRequired": [
            "Confirm target fit",
            "Assign P0 owners",
            "Approve build, test and cutover evidence",
        ],
        "boundary": "No project progress, cost or readiness is claimed without imported evidence.",
    }


def connector_requests(cards):
    return {
        "schemaVersion": "1.0",
        "mode": "REVIEW_ONLY",
        "requests": [
            {
                "adapter": "D365 metadata export",
                "purpose": "Verify object and extension seam",
                "approval": "Target environment owner",
                "write": False,
            },
            {
                "adapter": "Azure DevOps",
                "purpose": "Create reviewed work item/PR/build evidence payload",
                "approval": "Named backlog or repository owner",
                "write": True,
            },
            {
                "adapter": "Build/Test pipeline",
                "purpose": "Import sanitized result summary",
                "approval": "Engineering lead",
                "write": False,
            },
            {
                "adapter": "Monitoring",
                "purpose": "Import aggregate hypercare signals",
                "approval": "Operations owner",
                "write": False,
            },
        ],
        "candidateCount": len(cards),
    }


def benchmark(cards, cases):
    results = []
    for case in cases:
        matches = [
            card
            for card in cards
            if (not case.get("expectedType") or card["type"] == case["expectedType"])
            and (
                not case.get("expectedSignals")
                or any(signal in card["signals"] for signal in case["expectedSignals"])
            )
        ]
        passed = any(card["decision"] == case["expectedDecision"] for card in matches)
        results.append(
            {
                "id": case["id"],
                "status": "PASS" if passed else "FAIL",
                "matches": len(matches),
                "expectedDecision": case["expectedDecision"],
            }
        )
    return {
        "schemaVersion": "1.0",
        "results": results,
        "passRate": (
            sum(item["status"] == "PASS" for item in results) / len(results)
            if results
            else 0
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Create migration quality, evidence and connector-control artifacts."
    )
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--rules", type=Path, default=Path("config/migration-rules.json")
    )
    parser.add_argument(
        "--benchmark", type=Path, default=Path("assets/benchmark-cases.json")
    )
    parser.add_argument("--language", choices=("de", "en"), default="de")
    for label in SCHEMA_KEYS:
        parser.add_argument(f"--{label}", type=Path)
    args = parser.parse_args()
    cards = load_decisions(args.decisions)
    rules = read_json(args.rules)
    schema_root = Path(__file__).resolve().parents[1] / "schemas"
    validations = [
        validate_payload(label, path, schema_root)
        for label in SCHEMA_KEYS
        if (path := getattr(args, label.replace("-", "_")))
    ]
    input_paths = [args.decisions, args.rules, args.benchmark] + [
        getattr(args, key.replace("-", "_"))
        for key in SCHEMA_KEYS
        if getattr(args, key.replace("-", "_"))
    ]
    manifest = run_manifest(
        input_paths,
        "ax_migration_quality.py",
        {"rules": str(args.rules), "rulesVersion": rules.get("schemaVersion")},
    )
    root = args.out / "quality-control"
    write_json(root / "input-validation.json", {"validations": validations})
    write_json(root / "run-manifest.json", manifest)
    write_json(root / "evidence-ledger.json", evidence_ledger(cards, manifest))
    write_json(
        root / "executive-dashboard.json", dashboard(cards, validations, args.language)
    )
    write_json(root / "connector-requests.json", connector_requests(cards))
    write_json(
        root / "benchmark-results.json",
        benchmark(cards, read_json(args.benchmark).get("cases", [])),
    )
    print(
        f'{{"output": "{root}", "objectsAnalysed": {len(cards)}, "validatedInputs": {len(validations)}}}'
    )


if __name__ == "__main__":
    main()
