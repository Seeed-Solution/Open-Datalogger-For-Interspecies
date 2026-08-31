#!/usr/bin/env python3
import csv
import html
import sys
from pathlib import Path


DEFAULT_CSV = "/userdata/recamera_runtime_monitor.csv"
DEFAULT_HTML = "/userdata/recamera_runtime_report.html"


def to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def load_rows(path):
    with Path(path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def points(rows, key):
    heartbeat_rows = [row for row in rows if row.get("row_type") in ("service_start", "heartbeat")]
    if not heartbeat_rows:
        return ""

    max_x = max(to_float(row.get("uptime_seconds")) for row in heartbeat_rows) or 1.0
    max_y = max(to_float(row.get(key)) for row in heartbeat_rows) or 1.0
    coords = []
    for row in heartbeat_rows:
        x = 40 + to_float(row.get("uptime_seconds")) / max_x * 720
        y = 220 - to_float(row.get(key)) / max_y * 180
        coords.append(f"{x:.1f},{y:.1f}")
    return " ".join(coords)


def build_html(rows):
    start = rows[0]["timestamp_iso"] if rows else ""
    end = rows[-1]["timestamp_iso"] if rows else ""
    event_rows = [row for row in rows if row.get("row_type") == "target_event"]
    last_uptime = max((to_float(row.get("uptime_seconds")) for row in rows), default=0.0)
    last_energy = max((to_float(row.get("estimated_energy_wh")) for row in rows), default=0.0)

    event_table = "\n".join(
        "<tr>"
        f"<td>{html.escape(row.get('timestamp_iso', ''))}</td>"
        f"<td>{html.escape(row.get('event_class', ''))}</td>"
        f"<td>{html.escape(row.get('event_score', ''))}</td>"
        f"<td>{html.escape(row.get('gpio_expected', ''))}</td>"
        "</tr>"
        for row in event_rows[-100:]
    )

    uptime_hours = last_uptime / 3600.0
    energy_line = points(rows, "estimated_energy_wh")

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>reCamera Runtime Report</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; margin: 28px; color: #1f2933; }}
    h1 {{ font-size: 24px; }}
    .summary {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; margin: 20px 0; }}
    .metric {{ border: 1px solid #d9e2ec; padding: 12px; border-radius: 6px; }}
    .label {{ color: #627d98; font-size: 12px; }}
    .value {{ font-size: 22px; margin-top: 6px; }}
    svg {{ width: 100%; max-width: 860px; height: 260px; border: 1px solid #d9e2ec; border-radius: 6px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
    th, td {{ border-bottom: 1px solid #d9e2ec; padding: 8px; text-align: left; font-size: 13px; }}
    th {{ background: #f5f7fa; }}
  </style>
</head>
<body>
  <h1>reCamera Runtime Report</h1>
  <div class="summary">
    <div class="metric"><div class="label">Start</div><div class="value">{html.escape(start)}</div></div>
    <div class="metric"><div class="label">End</div><div class="value">{html.escape(end)}</div></div>
    <div class="metric"><div class="label">Runtime</div><div class="value">{uptime_hours:.2f} h</div></div>
    <div class="metric"><div class="label">Estimated Energy</div><div class="value">{last_energy:.2f} Wh</div></div>
  </div>
  <h2>Estimated Energy Curve</h2>
  <svg viewBox="0 0 820 260" role="img">
    <line x1="40" y1="220" x2="780" y2="220" stroke="#bcccdc" />
    <line x1="40" y1="20" x2="40" y2="220" stroke="#bcccdc" />
    <polyline fill="none" stroke="#2563eb" stroke-width="2.5" points="{energy_line}" />
    <text x="40" y="246" font-size="12" fill="#627d98">0h</text>
    <text x="730" y="246" font-size="12" fill="#627d98">{uptime_hours:.1f}h</text>
    <text x="48" y="32" font-size="12" fill="#627d98">{last_energy:.1f}Wh</text>
  </svg>
  <h2>Recent Target Events</h2>
  <table>
    <thead><tr><th>Time</th><th>Class</th><th>Score</th><th>Expected GPIO</th></tr></thead>
    <tbody>{event_table}</tbody>
  </table>
</body>
</html>
"""


def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_CSV
    html_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_HTML
    rows = load_rows(csv_path)
    Path(html_path).write_text(build_html(rows))
    print(f"Report written: {html_path}")


if __name__ == "__main__":
    main()
