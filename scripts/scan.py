#!/usr/bin/env python3
"""Scan the corpus of MCP servers with mcpscan and aggregate the results.

Read-only: mcpscan lists tool/resource/prompt definitions and never invokes a
tool. Only the servers listed in corpus.json are scanned. Results are written to
data/results.json (per-server) and data/summary.json (aggregate).

Usage:
    MCPSCAN="/path/to/mcpscan" python scripts/scan.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS = json.loads((ROOT / "scripts" / "corpus.json").read_text())
MCPSCAN = os.environ.get("MCPSCAN", "mcpscan")

SEVERITIES = ["critical", "high", "medium", "low", "info"]


def scan_one(entry: dict) -> dict:
    print(f"  scanning {entry['id']} ...", file=sys.stderr, flush=True)
    try:
        proc = subprocess.run(
            [*MCPSCAN.split(), entry["spec"], "--json"],
            capture_output=True, text=True, timeout=180,
        )
        data = json.loads(proc.stdout)
        findings = data.get("findings", [])
        by_sev = {s: sum(1 for f in findings if f.get("severity") == s) for s in SEVERITIES}
        by_cat: dict[str, int] = {}
        for f in findings:
            by_cat[f["category"]] = by_cat.get(f["category"], 0) + 1
        return {
            "id": entry["id"], "vendor": entry["vendor"], "transport": entry["transport"],
            "ok": True, "total_findings": len(findings),
            "by_severity": by_sev, "by_category": by_cat,
            "findings": findings,
        }
    except Exception as e:  # noqa: BLE001
        return {"id": entry["id"], "vendor": entry["vendor"], "transport": entry["transport"],
                "ok": False, "error": f"{type(e).__name__}: {str(e)[:160]}"}


def main() -> int:
    results = [scan_one(e) for e in CORPUS]
    scanned = [r for r in results if r.get("ok")]

    agg_sev = {s: 0 for s in SEVERITIES}
    agg_cat: dict[str, int] = {}
    servers_with = {s: 0 for s in SEVERITIES}
    for r in scanned:
        for s in SEVERITIES:
            agg_sev[s] += r["by_severity"][s]
            if r["by_severity"][s] > 0:
                servers_with[s] += 1
        for c, n in r["by_category"].items():
            agg_cat[c] = agg_cat.get(c, 0) + n

    n = len(scanned)
    # "at risk" = at least one medium-or-higher finding
    at_risk = sum(1 for r in scanned if any(r["by_severity"][s] for s in ("critical", "high", "medium")))
    summary = {
        "servers_in_corpus": len(CORPUS),
        "servers_scanned": n,
        "servers_failed": len(CORPUS) - n,
        "total_findings": sum(r["total_findings"] for r in scanned),
        "servers_at_risk": at_risk,
        "pct_at_risk": round(at_risk / n * 100) if n else 0,
        "findings_by_severity": agg_sev,
        "servers_with_severity": servers_with,
        "findings_by_category": dict(sorted(agg_cat.items(), key=lambda x: -x[1])),
    }

    (ROOT / "data" / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False))
    (ROOT / "data" / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
