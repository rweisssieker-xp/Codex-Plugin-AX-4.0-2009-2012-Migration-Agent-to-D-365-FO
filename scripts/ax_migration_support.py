"""Shared, dependency-free helpers for review-gated migration generators."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


SECRET_PATTERNS = {
    "connection_string": r"(?i)(server|database|uid|user id|password)\s*=",
    "access_token": r"(?i)\b(access[_ -]?token|client_secret|api[_ -]?key)\b",
    "private_key": r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----",
}


def timestamp():
    return datetime.now(timezone.utc).isoformat()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def scan_text(text):
    findings = []
    for category, pattern in SECRET_PATTERNS.items():
        for number, line in enumerate(text.splitlines(), 1):
            if re.search(pattern, line):
                findings.append(
                    {
                        "category": category,
                        "line": number,
                        "action": "Remove or replace with a redacted reference.",
                    }
                )
    return findings


def scan_path(path):
    if not path.exists() or not path.is_file():
        return []
    try:
        return scan_text(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return [
            {
                "category": "binary_or_unknown",
                "line": 0,
                "action": "Review manually before import.",
            }
        ]


def run_manifest(input_paths, tool, configuration):
    return {
        "schemaVersion": "1.0",
        "runId": f"run-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
        "generatedAt": timestamp(),
        "tool": tool,
        "configuration": configuration,
        "inputs": [
            {"path": str(path), "sha256": digest(path), "bytes": path.stat().st_size}
            for path in input_paths
            if path.exists() and path.is_file()
        ],
        "mode": "REVIEW_ONLY",
    }
