#!/usr/bin/env python3
"""Generate 20 review-gated commerce integration capability artifacts."""
from __future__ import annotations
import argparse, json
from pathlib import Path
from ax_migration_inventory import discover
from ax_migration_compiler import decision_cards, markdown_table


def main():
    p = argparse.ArgumentParser()
    p.add_argument("input", type=Path)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    if not a.input.exists():
        p.error(f"Input does not exist: {a.input}")
    cards = decision_cards(discover(a.input))
    o = a.out / "commerce-integration-factory"
    o.mkdir(parents=True, exist_ok=True)
    specs = [
        (
            "Integration Landscape Excavator",
            "Discover external contracts, consumers and ownership",
        ),
        (
            "Canonical Commerce Contract Generator",
            "Define customer/product/price/order/inventory/delivery canonical contracts",
        ),
        ("API-Version Impact Radar", "Detect contract-version consumer/test impact"),
        (
            "Order Lifecycle Digital Twin",
            "Model order states across channel, CRM, ERP, WMS and carrier",
        ),
        (
            "Order-State Reconciler",
            "Reconcile missing, duplicate or conflicting status transitions",
        ),
        (
            "Available-to-Promise Truth Engine",
            "Validate availability/reservation/promise ownership",
        ),
        (
            "Pricing & Promotion Precedence Guardian",
            "Resolve ERP/shop/marketplace price and discount precedence",
        ),
        (
            "Product Catalog Drift Detector",
            "Detect product, variant, attribute and media drift",
        ),
        (
            "Customer Identity Resolver",
            "Prepare duplicate/consent/golden-record matching decisions",
        ),
        (
            "Lead-to-Cash Integrity Guard",
            "Trace lead, quote, order, credit, invoice and payment handoffs",
        ),
        (
            "Marketplace Settlement Reconciliation",
            "Reconcile orders, fees, refunds, tax and payout evidence",
        ),
        (
            "Dropship Exception Orchestrator",
            "Route supplier confirmation, shipment and cancellation exceptions",
        ),
        (
            "Fulfilment Promise Engine",
            "Explain delivery promise from stock, warehouse, supplier and carrier",
        ),
        (
            "Returns & Refunds Digital Twin",
            "Trace return, inspection, refund, inventory and accounting states",
        ),
        (
            "EDI Partner Decoder",
            "Document message, acknowledgement, error and test contracts",
        ),
        (
            "Event Replay & Quarantine Manager",
            "Define idempotency, dead-letter, replay and correction gates",
        ),
        (
            "Contract-Test Factory",
            "Generate provider/consumer and negative contract test plans",
        ),
        (
            "Autonomous Exception Router",
            "Classify and assign integration exceptions with approval",
        ),
        (
            "Channel Cutover Simulator",
            "Prepare channel cutover, reconciliation and rollback gates",
        ),
        (
            "Integration SLO & Business-Impact Governor",
            "Link latency/errors/backlog to business impact and owner",
        ),
    ]
    catalog = []
    for i, (title, outcome) in enumerate(specs, 1):
        key = f'{i:02d}-{title.lower().replace(" ","-").replace("&","and")}'
        catalog.append(
            {
                "id": i,
                "title": title,
                "outcome": outcome,
                "mode": "REVIEW_ONLY",
                "metric": "Exception resolution time, contract coverage and reconciliation completeness",
                "guardrail": "No order, price, stock, refund, customer merge, replay or external write without approved connector and owner",
                "killCondition": "Stop if five qualified integration reviews show no reduction in manual resolution or incident duration",
                "rollback": "Discard generated artifact; retain source evidence and existing production controls",
            }
        )
        rows = [
            {
                "object": c["object"],
                "signals": ", ".join(c["signals"]) or c["type"],
                "requiredEvidence": "Contract, owner, consumer, test, rollback and business impact",
            }
            for c in cards
            if c["signals"]
        ] or [
            {
                "object": "External system inventory",
                "signals": "not supplied",
                "requiredEvidence": "Endpoint, auth owner, schema, SLA, consumer and rollback",
            }
        ]
        lines = [
            f"# {title}",
            "",
            outcome,
            "",
            "Generated from static AX evidence. It neither connects to nor modifies external systems.",
            "",
        ] + markdown_table(
            rows,
            [
                ("Object/integration", "object"),
                ("Signals", "signals"),
                ("Required evidence", "requiredEvidence"),
            ],
        )
        (o / f"{key}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (o / "commerce-usp-catalog.json").write_text(
        json.dumps(
            {
                "schemaVersion": "1.0",
                "claimBoundary": "All capabilities are review-gated templates until approved channel/CRM/WMS/EDI connectors and runtime evidence are supplied.",
                "usps": catalog,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    contract = {
        "schemaVersion": "1.0",
        "mode": "REVIEW_ONLY",
        "canonicalEntities": [
            "Customer",
            "Product",
            "Price",
            "Order",
            "OrderLine",
            "Inventory",
            "Shipment",
            "Return",
            "Refund",
            "Settlement",
        ],
        "requiredFields": [
            "externalId",
            "sourceSystem",
            "eventId",
            "version",
            "occurredAt",
            "legalEntity",
            "idempotencyKey",
        ],
        "safety": [
            "No credentials",
            "No auto-replay",
            "No auto-refund/cancel",
            "No inventory/price update without owner approval",
            "Dead-letter and rollback required",
        ],
    }
    (o / "canonical-contract-template.json").write_text(
        json.dumps(contract, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(o),
                "capabilities": len(specs),
                "objectsAnalysed": len(cards),
                "mode": "REVIEW_ONLY",
            }
        )
    )


if __name__ == "__main__":
    main()
