# Quality, reproducibility and connectors

Run the quality control pack after producing `decision-compiler.json`:

```powershell
python scripts/ax_migration_quality.py --decisions <output>\decision-compiler.json --out <output>
```

It adds input validation, secret scanning, schema references, a versioned rule audit, input and run hashes, an evidence ledger, an evidence-labelled executive dashboard, benchmark results and connector request payloads.

## Connector boundary

Connector requests are not connections. D365 metadata export, Azure DevOps, build/test and monitoring adapters remain disabled until a project owner explicitly authorizes the connector and each external write. No credentials are accepted in evidence files.

## Languages

Generated data fields are language-neutral. Use `--language de|en` in project-facing prompts and have the accountable owner approve translated business terms before use in UAT or governance.
