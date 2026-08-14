#!/usr/bin/env python3
"""First-pass, offline AX 2009/2012 migration inventory.

This is intentionally conservative: signals are evidence for review, not proof that
an object is customized, unused, or compatible with D365 F&O.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TEXT_EXTENSIONS = {".xpo", ".xpp", ".txt", ".xml", ".sql", ".cs", ".config"}
OBJECT_PATTERNS = [
    (
        re.compile(
            r"^\s*\*\*\*Element:\s*(Class|Table|Form|MenuItem|Query|View|Map|BaseEnum|ExtendedDataType|Report|SecurityRole|SecurityDuty|SecurityPrivilege|Service|DataEntity)\s+(.+?)\s*$",
            re.I | re.M,
        ),
        "xpo",
    ),
    (
        re.compile(
            r"^\s*(class|table|form|enum|query|view)\s+([A-Za-z_][A-Za-z0-9_]*)",
            re.I | re.M,
        ),
        "source",
    ),
]
SIGNALS = {
    "direct_sql": re.compile(
        r"\b(Connection|Statement|createStatement|executeQuery|executeUpdate|insert_recordset|update_recordset|delete_from)\b|\b(SELECT|INSERT|UPDATE|DELETE)\s+.+\s+\bFROM\b",
        re.I,
    ),
    "aif_or_service": re.compile(
        r"\b(Aif|Ax[A-Za-z]*Service|ServiceOperation|BusinessConnector|SOAP|WSDL)\b",
        re.I,
    ),
    "ssrs_or_morphx_report": re.compile(
        r"\b(SrsReport|SSRS|RunBaseReport|ReportRun|PrintMgmt)\b", re.I
    ),
    "batch": re.compile(
        r"\b(RunBaseBatch|BatchHeader|BatchInfo|canGoBatch|runsImpersonated)\b", re.I
    ),
    "security": re.compile(
        r"\b(SecurityRole|SecurityDuty|SecurityPrivilege|AccessRight|XDS|hasSecurityKeyAccess)\b",
        re.I,
    ),
    "client_or_legacy_api": re.compile(
        r"\b(WinApi|COM|CLRInterop|DotNet|FileIoPermission|WinAPIServer|runAs)\b", re.I
    ),
    "transaction_external_call": re.compile(
        r"ttsBegin[\s\S]{0,300}\b(WinApi|CLRInterop|executeQuery|createStatement|Http|WebRequest)\b",
        re.I,
    ),
    "cross_company": re.compile(r"\b(crossCompany|changeCompany)\b", re.I),
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def object_type(value: str) -> str:
    normalized = value.lower().replace(" ", "")
    return {
        "extendeddatatype": "EDT",
        "baseenum": "Enum",
        "menuitem": "MenuItem",
        "securityrole": "SecurityRole",
        "securityduty": "SecurityDuty",
        "securityprivilege": "SecurityPrivilege",
        "dataentity": "DataEntity",
    }.get(normalized, value.title())


def inferred_classification(kind: str, signals: list[str]) -> tuple[str, int, str]:
    if kind in {"SecurityRole", "SecurityDuty", "SecurityPrivilege"}:
        return (
            "REBUILD",
            3,
            "Security design needs duty/privilege and segregation-of-duties validation.",
        )
    if "direct_sql" in signals or "client_or_legacy_api" in signals:
        return "REBUILD", 4, "Unsupported or high-risk technical pattern detected."
    if "aif_or_service" in signals or "ssrs_or_morphx_report" in signals:
        return (
            "REBUILD",
            3,
            "Legacy integration/reporting pattern requires D365 target design.",
        )
    if kind in {
        "Table",
        "EDT",
        "Enum",
        "Form",
        "Class",
        "MenuItem",
        "Service",
        "DataEntity",
    }:
        return (
            "EXTEND",
            2,
            "Candidate for supported extensibility; confirm D365 standard fit and extension point.",
        )
    return "STANDARD", 1, "No migration-risk signal detected by first-pass inventory."


def discover(path: Path) -> list[dict]:
    records: list[dict] = []
    paths = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()]
    for file in paths:
        if file.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        try:
            text = file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits: dict[tuple[str, str], tuple[int, int]] = {}
        for pattern, source in OBJECT_PATTERNS:
            for match in pattern.finditer(text):
                kind, name = object_type(match.group(1)), match.group(2).strip().strip(
                    ";"
                )
                if len(name) < 2 or name.lower() in {"extends", "implements"}:
                    continue
                hits.setdefault(
                    (kind, name), (text[: match.start()].count("\n") + 1, match.start())
                )
        if not hits:
            hits[("Script", file.stem)] = (1, 0)
        ordered = sorted(
            (start, line, kind, name) for (kind, name), (line, start) in hits.items()
        )
        local_names = {name for _, _, _, name in ordered}
        for index, (start, line, kind, name) in enumerate(ordered):
            end = ordered[index + 1][0] if index + 1 < len(ordered) else len(text)
            body = text[start:end]
            found_signals = [
                signal for signal, pattern in SIGNALS.items() if pattern.search(body)
            ]
            classification, risk, rationale = inferred_classification(
                kind, found_signals
            )
            dependencies = sorted(
                other
                for other in local_names - {name}
                if re.search(rf"\b{re.escape(other)}\b", body)
            )
            records.append(
                {
                    "id": f"{kind}:{name}:{file.name}:{line}",
                    "name": name,
                    "type": kind,
                    "source": str(file),
                    "line": line,
                    "signals": found_signals,
                    "classification": classification,
                    "classificationBasis": rationale,
                    "risk": risk,
                    "confidence": "low",
                    "reviewStatus": "unreviewed",
                    "evidence": [f"{file}:{line}"],
                    "dependencies": dependencies,
                }
            )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create a reviewable AX migration inventory."
    )
    parser.add_argument("input", type=Path, help="AX source directory or export file")
    parser.add_argument("--out", type=Path, required=True, help="Output directory")
    args = parser.parse_args()
    if not args.input.exists():
        parser.error(f"Input does not exist: {args.input}")
    args.out.mkdir(parents=True, exist_ok=True)
    records = discover(args.input)
    counts = Counter(row["classification"] for row in records)
    type_counts = Counter(row["type"] for row in records)
    inputs = (
        [args.input]
        if args.input.is_file()
        else [p for p in args.input.rglob("*") if p.is_file()]
    )
    manifest = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "tool": "ax_migration_inventory.py",
        "limitations": [
            "Heuristic first pass; classifications and signals require reviewer validation.",
            "No model-store, runtime telemetry, D365 metadata, or SQL database correlation was performed.",
        ],
        "inputs": [
            {"path": str(p), "bytes": p.stat().st_size, "sha256": sha256(p)}
            for p in inputs
        ],
    }
    inventory = {
        "schemaVersion": "1.0",
        "summary": {
            "objectsAnalysed": len(records),
            "classifications": counts,
            "objectTypes": type_counts,
        },
        "objects": records,
    }
    (args.out / "input-manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    (args.out / "inventory.json").write_text(
        json.dumps(inventory, indent=2, default=dict), encoding="utf-8"
    )
    lines = [
        "# AX 2012 → D365 F&O migration backlog",
        "",
        "## First-pass portfolio",
        "",
        f"- {len(records):,} AX objects analysed",
        f"- {counts['STANDARD']:,} Microsoft standard candidates",
        f"- {counts['REMOVE']:,} obsolete/removal candidates",
        f"- {counts['EXTEND']:,} extension candidates",
        f"- {counts['REBUILD']:,} manual redesign required",
        "",
        "## Reviewer queue",
        "",
        "| Object | Type | Classification | Risk | Signals | Evidence |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in sorted(
        (r for r in records if r["classification"] != "STANDARD"),
        key=lambda r: (-r["risk"], r["name"]),
    ):
        lines.append(
            f"| {row['name']} | {row['type']} | {row['classification']} | {row['risk']}/5 | {', '.join(row['signals']) or '—'} | `{row['source']}:{row['line']}` |"
        )
    lines += [
        "",
        "## Limitation",
        "",
        "This is a heuristic inventory, not a supportability or business-usage decision. Validate every non-standard row against AX metadata, D365 extensibility options, business ownership, and tests.",
    ]
    (args.out / "migration-backlog.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(args.out),
                "objectsAnalysed": len(records),
                "classifications": counts,
            },
            default=dict,
        )
    )


if __name__ == "__main__":
    main()
