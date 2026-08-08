#!/usr/bin/env python3
"""Generate SVG charts from data/summary.json (no external deps)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S = json.loads((ROOT / "data" / "summary.json").read_text())

INK, PANEL, LINE, TEXT, DIM = "#0d1014", "#171d25", "#232c37", "#e6eaf0", "#9aa6b4"
SEV_COLOR = {"critical": "#e5626a", "high": "#f2a93b", "medium": "#f2c14b",
             "low": "#6fb6b0", "info": "#6b7787"}
CAT_COLOR = "#f2a93b"


def _bars(title, items, colorf, unit=""):
    # items: list of (label, value)
    W, rowh, pad, top, labelw = 640, 30, 20, 56, 190
    maxv = max((v for _, v in items), default=1) or 1
    barmax = W - labelw - pad - 70
    H = top + rowh * len(items) + 16
    rows = [f'<rect width="{W}" height="{H}" rx="10" fill="{INK}"/>',
            f'<text x="{pad}" y="32" fill="{TEXT}" font-size="15" font-weight="700">{title}</text>']
    for i, (label, v) in enumerate(items):
        y = top + i * rowh
        bw = int(v / maxv * barmax)
        c = colorf(label)
        rows.append(f'<text x="{pad}" y="{y+14}" fill="{DIM}" font-size="12">{label}</text>')
        rows.append(f'<rect x="{labelw}" y="{y+2}" width="{max(bw,2)}" height="16" rx="3" fill="{c}"/>')
        rows.append(f'<text x="{labelw+max(bw,2)+8}" y="{y+14}" fill="{TEXT}" font-size="12" '
                    f'font-weight="600">{v}{unit}</text>')
    body = "\n".join(rows)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'font-family="ui-monospace,SFMono-Regular,Menlo,monospace">\n{body}\n</svg>')


# severity chart
sev = S["findings_by_severity"]
sev_items = [(k, sev[k]) for k in ("critical", "high", "medium", "low", "info")]
(ROOT / "assets" / "severity.svg").write_text(
    _bars(f"Findings by severity ({S['total_findings']} total, {S['servers_scanned']} servers)",
          sev_items, lambda k: SEV_COLOR[k]))

# category chart
cat = S["findings_by_category"]
cat_items = list(cat.items())
(ROOT / "assets" / "category.svg").write_text(
    _bars("Findings by category", cat_items, lambda _k: CAT_COLOR))

print("charts written:", [p.name for p in (ROOT / "assets").glob("*.svg")])
