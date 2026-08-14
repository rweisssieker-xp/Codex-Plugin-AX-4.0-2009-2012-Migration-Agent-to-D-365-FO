# AX 4.0 / 2009 / 2012 → D365 F&O Migration Agent

Evidence-led Codex plugin for modernizing Microsoft Dynamics AX customizations into reviewable Dynamics 365 Finance & Operations decisions and delivery artifacts.

## What it does

- Discovers AX XPO/repository objects, X++ risk signals, direct SQL, integrations, reports, security and ISV evidence.
- Classifies candidates as `STANDARD`, `EXTEND`, `REBUILD` or `REMOVE` with traceable evidence and effort hypotheses.
- Produces review-gated target architecture, proposals, test strategy, data migration, commerce, governance, cutover, hypercare and executive/process-owner artifacts.
- Generates a quality-control pack with input schemas, secret scan, rule audit, evidence ledger, benchmark, dashboard and connector requests.

## Safety boundary

The plugin is evidence-led and `REVIEW_ONLY`. It never stores credentials, connects to D365 by itself, reads/writes production data, compiles/deploys X++, creates Azure DevOps items, or approves cutover/go-live decisions. Human owners must approve every external action.

## Quick start

```powershell
python scripts/ax_migration_compiler.py <AX-export-or-source> --out <output-folder> --generate-proposals --review-room --usp-suite --executive-suite --process-suite
python scripts/ax_migration_quality.py --decisions <output-folder>\decision-compiler.json --out <output-folder> --language de
```

## Validation

```powershell
python -m unittest discover -s tests
python C:\Users\reinerw\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .
```

## Marketplace readiness

The plugin includes a valid Codex manifest, privacy policy, terms, security policy, tests and a documented least-privilege connector boundary. Before enabling project-specific D365, Azure DevOps or monitoring apps, have the workspace owner review authentication, scopes, write actions, source boundaries, privacy, data residency and pilot-group access.

## License

No open-source license has been selected yet. Add a license before accepting external contributions or communicating reuse rights.

## Support

Use [GitHub Issues](https://github.com/rweisssieker-xp/Codex-Plugin-AX-4.0-2009-2012-Migration-Agent-to-D-365-FO/issues) for defects and feature requests. Do not include credentials, production data or personal data in issues.
