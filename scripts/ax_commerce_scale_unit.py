#!/usr/bin/env python3
"""Create review-gated Commerce Scale Unit operating artifacts."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from ax_migration_inventory import discover
from ax_migration_compiler import decision_cards


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if not a.input.exists():
        p.error(f"Input does not exist: {a.input}")
    cards = decision_cards(discover(a.input))
    o = a.out / "commerce-scale-unit"
    o.mkdir(parents=True, exist_ok=True)
    specs = [
        ("Channel Launch Factory", "Repeatable channel launch gates"),
        (
            "Country Expansion Readiness Engine",
            "Country/legal entity/tax/carrier readiness",
        ),
        ("Commerce Unit Economics Twin", "Channel margin/fee/returns assumptions"),
        (
            "Assortment-to-Channel Optimizer",
            "Assortment approval and data-quality gates",
        ),
        (
            "Global Inventory Allocation Governor",
            "Inventory/service-level allocation rules",
        ),
        ("Marketplace Seller Health Sentinel", "Seller SLA/risk review"),
        ("Commerce Incident Command Cell", "Business-impact incident operation"),
        (
            "Reusable Partner Blueprint Library",
            "Approved partner/EDI/WMS/carrier patterns",
        ),
        (
            "Demand-to-Fulfilment Shock Simulator",
            "Demand/supply/carrier contingency scenarios",
        ),
        ("Commerce Operating Review Autopilot", "Action-led weekly/monthly review"),
    ]
    catalog = []
    for i, (title, outcome) in enumerate(specs, 1):
        key = f'{i:02d}-{title.lower().replace(" ","-").replace("&","and")}'
        catalog.append(
            {
                "id": i,
                "title": title,
                "outcome": outcome,
                "metric": "Launch cycle time, SLA/exception resolution, channel readiness and evidence completeness",
                "guardrail": "No channel launch, price, stock, assortment or external write without owner, contract test and rollback",
                "killCondition": "Stop if five qualified reviews do not reduce launch/review cycle time",
                "rollback": "Discard generated plan; preserve existing channel controls",
            }
        )
        content = f"# {title}\n\n{outcome}.\n\n## Evidence gates\n\n- Named channel and business owner\n- Approved canonical contract and consumer list\n- Test, reconciliation, monitoring and rollback evidence\n- Explicit go/no-go decision\n\n## Current migration evidence\n\n{len(cards)} static AX objects analysed. External channel, demand, cost, SLA and operational data must be supplied before this artifact can make a readiness claim.\n"
        (o / f"{key}.md").write_text(content, encoding="utf-8")
    (o / "commerce-scale-unit-catalog.json").write_text(
        json.dumps(
            {"schemaVersion": "1.0", "mode": "REVIEW_ONLY", "usps": catalog}, indent=2
        ),
        encoding="utf-8",
    )
    (o / "operating-contract.json").write_text(
        json.dumps(
            {
                "autonomous": [
                    "Prepare launch/incident/review packs",
                    "Detect missing evidence",
                    "Prioritize unowned gates",
                ],
                "humanOnly": [
                    "Approve launches",
                    "Set price/assortment/inventory policy",
                    "Commit spend/contracts",
                    "Execute external writes",
                ],
                "boundary": "No connector credentials or external operations.",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {"output": str(o), "capabilities": 10, "objectsAnalysed": len(cards)}
        )
    )


if __name__ == "__main__":
    main()
