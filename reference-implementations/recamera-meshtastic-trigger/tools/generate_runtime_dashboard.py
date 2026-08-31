#!/usr/bin/env python3
import argparse
import csv
import html
import json
import shutil
import subprocess
from collections import Counter
from datetime import datetime
from pathlib import Path


REMOTE_CSV = "/userdata/recamera_runtime_monitor.csv"
DEFAULT_POWER_WATTS = 5.6
DEFAULT_GAP_SECONDS = 150


def parse_time(value):
    return datetime.fromisoformat(value)


def to_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def load_rows(path):
    with Path(path).open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        row["_dt"] = parse_time(row["timestamp_iso"])
        row["_ts"] = row["_dt"].timestamp() * 1000
    rows.sort(key=lambda row: row["_dt"])
    return rows


def copy_local_csv(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def fetch_remote_csv(args, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    remote = f"{args.user}@{args.host}:{args.remote_csv}"
    command = [
        "scp",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        remote,
        str(destination),
    ]
    if args.use_sshpass_env:
        command = ["sshpass", "-e"] + command
    subprocess.run(command, check=True)
    return destination


def detect_segments(rows, gap_seconds):
    heartbeat_rows = [
        row for row in rows if row.get("row_type") in ("service_start", "heartbeat")
    ]
    segments = []
    offline_segments = []
    reboots = []
    if not heartbeat_rows:
        return segments, offline_segments, reboots

    segment_start = heartbeat_rows[0]
    previous = heartbeat_rows[0]
    for current in heartbeat_rows[1:]:
        gap = (current["_dt"] - previous["_dt"]).total_seconds()
        boot_changed = current.get("boot_id") != previous.get("boot_id")
        if gap > gap_seconds or boot_changed:
            segments.append({"start": segment_start, "end": previous})
            offline_segments.append(
                {
                    "start": previous,
                    "end": current,
                    "seconds": gap,
                    "reason": "reboot" if boot_changed else "heartbeat_gap",
                }
            )
            if boot_changed:
                reboots.append({"from": previous, "to": current, "gap_seconds": gap})
            segment_start = current
        previous = current
    segments.append({"start": segment_start, "end": heartbeat_rows[-1]})
    return segments, offline_segments, reboots


def summarize(rows, gap_seconds, power_watts):
    event_rows = [row for row in rows if row.get("row_type") == "target_event"]
    heartbeat_rows = [
        row for row in rows if row.get("row_type") in ("service_start", "heartbeat")
    ]
    segments, offline_segments, reboots = detect_segments(rows, gap_seconds)
    counts = Counter(row.get("event_class") or "unknown" for row in event_rows)

    first = rows[0]
    last = rows[-1]
    observed_seconds = (last["_dt"] - first["_dt"]).total_seconds()
    online_seconds = sum(
        max(0.0, (segment["end"]["_dt"] - segment["start"]["_dt"]).total_seconds())
        for segment in segments
    )
    offline_seconds = sum(segment["seconds"] for segment in offline_segments)

    return {
        "first": first,
        "last": last,
        "observed_seconds": observed_seconds,
        "online_seconds": online_seconds,
        "offline_seconds": offline_seconds,
        "window_energy_wh": online_seconds / 3600.0 * power_watts,
        "latest_boot_energy_wh": to_float(last.get("estimated_energy_wh")),
        "power_watts": power_watts,
        "gap_seconds": gap_seconds,
        "row_count": len(rows),
        "heartbeat_count": len(heartbeat_rows),
        "event_count": len(event_rows),
        "counts": counts,
        "boot_ids": sorted({row.get("boot_id") for row in rows if row.get("boot_id")}),
        "segments": segments,
        "offline_segments": offline_segments,
        "reboots": reboots,
        "events": event_rows,
    }


def fmt_minutes(seconds):
    return f"{seconds / 60.0:.1f}"


def fmt_time(row):
    return row.get("timestamp_iso", "")


def chart_json(rows, summary):
    chart_rows = []
    previous_heartbeat = None
    cumulative_online_seconds = 0.0
    for row in rows:
        window_estimated_energy_wh = ""
        if row.get("row_type") in ("service_start", "heartbeat"):
            if previous_heartbeat is not None:
                gap = (row["_dt"] - previous_heartbeat["_dt"]).total_seconds()
                same_boot = row.get("boot_id") == previous_heartbeat.get("boot_id")
                if same_boot and gap <= summary["gap_seconds"]:
                    cumulative_online_seconds += max(0.0, gap)
            previous_heartbeat = row
            window_estimated_energy_wh = (
                cumulative_online_seconds / 3600.0 * summary["power_watts"]
            )

        chart_rows.append(
            {
                "ts": row["_ts"],
                "timestamp_iso": row.get("timestamp_iso", ""),
                "row_type": row.get("row_type", ""),
                "boot_id": row.get("boot_id", ""),
                "uptime_seconds": to_float(row.get("uptime_seconds")),
                "estimated_energy_wh": to_float(row.get("estimated_energy_wh")),
                "window_estimated_energy_wh": window_estimated_energy_wh,
                "estimated_battery_used_pct": to_float(
                    row.get("estimated_battery_used_pct")
                ),
                "inference_status": row.get("inference_status", ""),
                "inference_actual_fps": row.get("inference_actual_fps", ""),
                "frames_seen": to_float(row.get("frames_seen")),
                "detections_seen": to_float(row.get("detections_seen")),
                "target_classes_seen": row.get("target_classes_seen", ""),
                "target_seen_count": to_float(row.get("target_seen_count")),
                "target_max_score": to_float(row.get("target_max_score")),
                "event_class": row.get("event_class", ""),
                "event_score": row.get("event_score", ""),
                "gpio_expected": row.get("gpio_expected", ""),
            }
        )

    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "start": fmt_time(summary["first"]),
        "end": fmt_time(summary["last"]),
        "observed_minutes": round(summary["observed_seconds"] / 60.0, 2),
        "online_minutes": round(summary["online_seconds"] / 60.0, 2),
        "offline_minutes": round(summary["offline_seconds"] / 60.0, 2),
        "window_energy_wh": round(summary["window_energy_wh"], 3),
        "latest_boot_energy_wh": round(summary["latest_boot_energy_wh"], 3),
        "power_watts": summary["power_watts"],
        "row_count": summary["row_count"],
        "heartbeat_count": summary["heartbeat_count"],
        "event_count": summary["event_count"],
        "class_counts": dict(summary["counts"]),
        "boot_count": len(summary["boot_ids"]),
        "rows": chart_rows,
        "segments": [
            {
                "start": segment["start"]["_ts"],
                "end": segment["end"]["_ts"],
                "start_label": fmt_time(segment["start"]),
                "end_label": fmt_time(segment["end"]),
            }
            for segment in summary["segments"]
        ],
        "offline_segments": [
            {
                "start": segment["start"]["_ts"],
                "end": segment["end"]["_ts"],
                "start_label": fmt_time(segment["start"]),
                "end_label": fmt_time(segment["end"]),
                "minutes": round(segment["seconds"] / 60.0, 2),
                "reason": segment["reason"],
            }
            for segment in summary["offline_segments"]
        ],
    }


def build_html(rows, summary, source_csv_name):
    data = chart_json(rows, summary)
    recent_events = list(reversed(summary["events"][-12:]))
    recent_event_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(event.get('timestamp_iso', ''))}</td>"
        f"<td>{html.escape(event.get('event_class', ''))}</td>"
        f"<td>{html.escape(event.get('event_score', ''))}</td>"
        f"<td>{html.escape(event.get('gpio_expected', ''))}</td>"
        "</tr>"
        for event in recent_events
    )
    if not recent_event_rows:
        recent_event_rows = '<tr><td colspan="4">No target events recorded.</td></tr>'

    offline_rows = "\n".join(
        "<tr>"
        f"<td>{html.escape(segment['start_label'])}</td>"
        f"<td>{html.escape(segment['end_label'])}</td>"
        f"<td>{segment['minutes']:.2f}</td>"
        f"<td>{html.escape(segment['reason'])}</td>"
        "</tr>"
        for segment in data["offline_segments"]
    )
    if not offline_rows:
        offline_rows = '<tr><td colspan="4">No offline gaps or reboot gaps detected.</td></tr>'

    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>reCamera Runtime Dashboard</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f7f9fc;
      --surface: #ffffff;
      --text: #17202a;
      --muted: #697789;
      --border: #d7dee8;
      --online: #2f9e44;
      --offline: #d9480f;
      --person: #1c7ed6;
      --cat: #ae3ec9;
      --heartbeat: #f08c00;
      --energy: #0ca678;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      padding: 24px;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{ max-width: 1180px; margin: 0 auto; }}
    h1 {{ font-size: 26px; margin: 0 0 4px; letter-spacing: 0; }}
    h2 {{ font-size: 16px; margin: 22px 0 10px; }}
    .subtitle {{ color: var(--muted); font-size: 13px; }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 10px;
      margin: 18px 0;
    }}
    .metric {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 12px;
      min-height: 78px;
    }}
    .metric label {{ display: block; color: var(--muted); font-size: 12px; }}
    .metric strong {{ display: block; font-size: 24px; margin-top: 5px; }}
    .metric span {{ display: block; color: var(--muted); font-size: 12px; margin-top: 4px; }}
    .grid {{ display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(300px, .85fr); gap: 16px; }}
    .panel {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 14px;
    }}
    svg {{ width: 100%; display: block; }}
    .frame {{ fill: none; stroke: var(--border); }}
    .axis {{ stroke: #a8b3c2; stroke-width: 1; }}
    text {{ fill: var(--text); font-size: 12px; }}
    .muted {{ fill: var(--muted); }}
    .legend {{ display: flex; gap: 14px; flex-wrap: wrap; margin: 8px 0 0; color: var(--muted); font-size: 12px; }}
    .key {{ display: inline-flex; align-items: center; gap: 6px; }}
    .swatch {{ width: 10px; height: 10px; display: inline-block; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-bottom: 1px solid var(--border); padding: 8px 6px; text-align: left; font-size: 13px; }}
    th {{ color: var(--muted); font-weight: 600; background: #fbfcfe; }}
    .tooltip {{
      position: absolute;
      z-index: 3;
      pointer-events: none;
      opacity: 0;
      background: #111827;
      color: #fff;
      padding: 7px 9px;
      border-radius: 5px;
      font-size: 12px;
      max-width: 270px;
    }}
    @media (max-width: 820px) {{
      body {{ padding: 14px; }}
      .metrics {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }}
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
<main id="runtime-dashboard">
  <h1>reCamera Runtime Dashboard</h1>
  <div class="subtitle">
    {html.escape(data["start"])} to {html.escape(data["end"])} · source:
    {html.escape(source_csv_name)} · generated {html.escape(data["generated_at"])}
  </div>

  <section class="metrics">
    <div class="metric"><label>Observed Window</label><strong>{data["observed_minutes"]:.1f} min</strong><span>{data["row_count"]} rows</span></div>
    <div class="metric"><label>Online Time</label><strong>{data["online_minutes"]:.1f} min</strong><span>{data["offline_minutes"]:.1f} min offline gaps</span></div>
    <div class="metric"><label>Target Events</label><strong>{data["event_count"]}</strong><span>{html.escape(", ".join(f"{k} {v}" for k, v in data["class_counts"].items()) or "none")}</span></div>
    <div class="metric"><label>Estimated Energy</label><strong>{data["window_energy_wh"]:.2f} Wh</strong><span>window estimate at {data["power_watts"]:g} W</span></div>
  </section>

  <section class="grid">
    <div class="panel">
      <h2>Online Timeline And Target Events</h2>
      <svg id="timeline" viewBox="0 0 820 240" role="img" aria-label="online timeline and target events"></svg>
      <div class="legend">
        <span class="key"><span class="swatch" style="background:var(--online)"></span>online</span>
        <span class="key"><span class="swatch" style="background:var(--offline)"></span>offline/reboot gap</span>
        <span class="key"><span class="swatch" style="background:var(--person)"></span>person</span>
        <span class="key"><span class="swatch" style="background:var(--cat)"></span>cat</span>
        <span class="key"><span class="swatch" style="background:var(--heartbeat)"></span>heartbeat</span>
      </div>
      <h2>Estimated Energy</h2>
      <svg id="energy" viewBox="0 0 820 220" role="img" aria-label="estimated energy curve"></svg>
    </div>
    <div class="panel">
      <h2>Events By Class</h2>
      <svg id="class-bars" viewBox="0 0 360 190" role="img" aria-label="events by class"></svg>
      <h2>Recent Target Events</h2>
      <table>
        <thead><tr><th>Time</th><th>Class</th><th>Score</th><th>GPIO</th></tr></thead>
        <tbody>{recent_event_rows}</tbody>
      </table>
      <h2>Offline Or Reboot Gaps</h2>
      <table>
        <thead><tr><th>From</th><th>To</th><th>Min</th><th>Reason</th></tr></thead>
        <tbody>{offline_rows}</tbody>
      </table>
    </div>
  </section>
  <div class="tooltip" id="tooltip"></div>
</main>
<script>
(() => {{
  const data = {json.dumps(data, ensure_ascii=False)};
  const rows = data.rows;
  const heartbeats = rows.filter(row => row.row_type === "service_start" || row.row_type === "heartbeat");
  const events = rows.filter(row => row.row_type === "target_event");
  const root = document.getElementById("runtime-dashboard");
  const tooltip = document.getElementById("tooltip");
  const start = Math.min(...rows.map(row => row.ts));
  const end = Math.max(...rows.map(row => row.ts));
  const formatTime = ms => new Date(ms).toLocaleTimeString("zh-CN", {{ hour: "2-digit", minute: "2-digit", second: "2-digit" }});
  const colorFor = klass => klass === "cat" ? "var(--cat)" : klass === "person" ? "var(--person)" : "#495057";

  function xScale(ms, left, width) {{
    return left + ((ms - start) / Math.max(1, end - start)) * width;
  }}

  function svgEl(name, attrs, parent) {{
    const node = document.createElementNS("http://www.w3.org/2000/svg", name);
    Object.entries(attrs || {{}}).forEach(([key, value]) => node.setAttribute(key, value));
    if (parent) parent.appendChild(node);
    return node;
  }}

  function showTip(event, text) {{
    const bounds = root.getBoundingClientRect();
    tooltip.innerHTML = text;
    tooltip.style.left = `${{event.clientX - bounds.left + 12}}px`;
    tooltip.style.top = `${{event.clientY - bounds.top + 12}}px`;
    tooltip.style.opacity = 1;
  }}

  function hideTip() {{
    tooltip.style.opacity = 0;
  }}

  function drawTimeline() {{
    const svg = document.getElementById("timeline");
    const left = 74, top = 30, width = 680, height = 152;
    svg.innerHTML = "";
    svgEl("rect", {{ x: left, y: top, width, height, class: "frame" }}, svg);
    data.segments.forEach(segment => {{
      const x1 = xScale(segment.start, left, width);
      const x2 = xScale(segment.end, left, width);
      const rect = svgEl("rect", {{ x: x1, y: 82, width: Math.max(2, x2 - x1), height: 32, fill: "var(--online)", opacity: "0.78" }}, svg);
      rect.addEventListener("mousemove", event => showTip(event, `online<br>${{segment.start_label}}<br>${{segment.end_label}}`));
      rect.addEventListener("mouseleave", hideTip);
    }});
    data.offline_segments.forEach(segment => {{
      const x1 = xScale(segment.start, left, width);
      const x2 = xScale(segment.end, left, width);
      const rect = svgEl("rect", {{ x: x1, y: 82, width: Math.max(2, x2 - x1), height: 32, fill: "var(--offline)", opacity: "0.75" }}, svg);
      rect.addEventListener("mousemove", event => showTip(event, `${{segment.reason}}<br>${{segment.start_label}}<br>${{segment.end_label}}<br>${{segment.minutes}} min`));
      rect.addEventListener("mouseleave", hideTip);
    }});
    heartbeats.forEach(row => svgEl("circle", {{ cx: xScale(row.ts, left, width), cy: 145, r: 2.7, fill: "var(--heartbeat)", opacity: "0.84" }}, svg));
    events.forEach(row => {{
      const cx = xScale(row.ts, left, width);
      const group = svgEl("g", {{}}, svg);
      svgEl("line", {{ x1: cx, x2: cx, y1: 42, y2: 176, stroke: colorFor(row.event_class), "stroke-width": 1.6, opacity: "0.76" }}, group);
      svgEl("circle", {{ cx, cy: row.event_class === "cat" ? 58 : 43, r: 5.7, fill: colorFor(row.event_class) }}, group);
      group.addEventListener("mousemove", event => showTip(event, `${{row.timestamp_iso}}<br>${{row.event_class}} score=${{row.event_score}}<br>GPIO ${{row.gpio_expected}}`));
      group.addEventListener("mouseleave", hideTip);
    }});
    [["Start", start, "start"], ["End", end, "end"]].forEach(([label, ms, anchor]) => {{
      const x = xScale(ms, left, width);
      svgEl("line", {{ x1: x, x2: x, y1: top + height, y2: top + height + 6, class: "axis" }}, svg);
      const text = svgEl("text", {{ x, y: top + height + 24, "text-anchor": anchor, class: "muted" }}, svg);
      text.textContent = `${{label}} ${{formatTime(ms)}}`;
    }});
    svgEl("text", {{ x: 16, y: 103, class: "muted" }}, svg).textContent = "Online";
    svgEl("text", {{ x: 16, y: 149, class: "muted" }}, svg).textContent = "Heartbeat";
  }}

  function drawEnergy() {{
    const svg = document.getElementById("energy");
    const left = 74, top = 24, width = 680, height = 138;
    svg.innerHTML = "";
    const values = heartbeats.map(row => row.window_estimated_energy_wh);
    const minY = Math.min(...values);
    const maxY = Math.max(...values);
    const yScale = value => top + height - ((value - minY) / Math.max(0.001, maxY - minY)) * height;
    svgEl("rect", {{ x: left, y: top, width, height, class: "frame" }}, svg);
    const points = heartbeats.map(row => `${{xScale(row.ts, left, width).toFixed(1)}},${{yScale(row.window_estimated_energy_wh).toFixed(1)}}`).join(" ");
    svgEl("polyline", {{ points, fill: "none", stroke: "var(--energy)", "stroke-width": 2.5 }}, svg);
    heartbeats.forEach(row => svgEl("circle", {{ cx: xScale(row.ts, left, width), cy: yScale(row.window_estimated_energy_wh), r: 2.7, fill: "var(--energy)", opacity: "0.74" }}, svg));
    svgEl("text", {{ x: 22, y: 32, class: "muted" }}, svg).textContent = "Wh";
    svgEl("text", {{ x: left - 8, y: yScale(maxY) + 4, "text-anchor": "end", class: "muted" }}, svg).textContent = maxY.toFixed(2);
    svgEl("text", {{ x: left - 8, y: yScale(minY) + 4, "text-anchor": "end", class: "muted" }}, svg).textContent = minY.toFixed(2);
    svgEl("text", {{ x: left + width, y: top + height + 28, "text-anchor": "end", class: "muted" }}, svg).textContent = "window cumulative estimate";
  }}

  function drawClassBars() {{
    const svg = document.getElementById("class-bars");
    const items = Object.entries(data.class_counts).map(([klass, count]) => ({{ klass, count }}));
    const maxCount = Math.max(1, ...items.map(item => item.count));
    const left = 74, top = 30, width = 225, barHeight = 30, gap = 18;
    svg.innerHTML = "";
    if (!items.length) {{
      svgEl("text", {{ x: 16, y: 86, class: "muted" }}, svg).textContent = "No target events recorded.";
      return;
    }}
    items.forEach((item, index) => {{
      const y = top + index * (barHeight + gap);
      svgEl("text", {{ x: 12, y: y + 20, class: "muted" }}, svg).textContent = item.klass;
      svgEl("rect", {{ x: left, y, width: width * item.count / maxCount, height: barHeight, fill: colorFor(item.klass), opacity: "0.86" }}, svg);
      svgEl("text", {{ x: left + width * item.count / maxCount + 8, y: y + 20 }}, svg).textContent = item.count;
    }});
  }}

  drawTimeline();
  drawEnergy();
  drawClassBars();
}})();
</script>
</body>
</html>
"""


def write_summary(summary, path):
    lines = [
        "# reCamera Runtime Summary",
        "",
        f"- Start: {fmt_time(summary['first'])}",
        f"- End: {fmt_time(summary['last'])}",
        f"- Observed window: {fmt_minutes(summary['observed_seconds'])} minutes",
        f"- Online time: {fmt_minutes(summary['online_seconds'])} minutes",
        f"- Offline/reboot gap time: {fmt_minutes(summary['offline_seconds'])} minutes",
        f"- Target events: {summary['event_count']}",
        f"- Class counts: {dict(summary['counts'])}",
        f"- Boot IDs: {len(summary['boot_ids'])}",
        f"- Window estimated energy: {summary['window_energy_wh']:.3f} Wh",
        f"- Latest boot cumulative energy: {summary['latest_boot_energy_wh']:.3f} Wh",
        "",
        "## Offline Or Reboot Gaps",
        "",
    ]
    if summary["offline_segments"]:
        for segment in summary["offline_segments"]:
            lines.append(
                f"- {fmt_time(segment['start'])} -> {fmt_time(segment['end'])}: "
                f"{fmt_minutes(segment['seconds'])} minutes, {segment['reason']}"
            )
    else:
        lines.append("- No offline gaps or reboot gaps detected.")

    lines.extend(["", "## Target Events", ""])
    if summary["events"]:
        for event in summary["events"]:
            lines.append(
                f"- {fmt_time(event)}: {event.get('event_class', '')} "
                f"score={event.get('event_score', '')}, gpio={event.get('gpio_expected', '')}"
            )
    else:
        lines.append("- No target events recorded.")

    Path(path).write_text("\n".join(lines) + "\n")


def timestamp_label():
    return datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Fetch or read reCamera runtime CSV and generate a dashboard."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--host", help="reCamera IP or hostname to fetch from with scp.")
    source.add_argument("--csv", help="Analyze an existing local CSV file.")
    parser.add_argument("--user", default="root", help="SSH username. Default: root.")
    parser.add_argument(
        "--remote-csv",
        default=REMOTE_CSV,
        help=f"Remote CSV path. Default: {REMOTE_CSV}",
    )
    parser.add_argument(
        "--use-sshpass-env",
        action="store_true",
        help="Wrap scp with sshpass -e. Set SSHPASS to the SSH password first.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parent / "reports"),
        help="Output directory for copied CSV, HTML, and summary.",
    )
    parser.add_argument(
        "--gap-seconds",
        type=float,
        default=DEFAULT_GAP_SECONDS,
        help="Heartbeat gap threshold for offline detection. Default: 150.",
    )
    parser.add_argument(
        "--power-watts",
        type=float,
        default=DEFAULT_POWER_WATTS,
        help="Power value for energy estimate. Default: 5.6.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = timestamp_label()
    copied_csv = output_dir / f"recamera_runtime_monitor_{stamp}.csv"

    if args.csv:
        copy_local_csv(Path(args.csv), copied_csv)
    else:
        fetch_remote_csv(args, copied_csv)

    rows = load_rows(copied_csv)
    if not rows:
        raise SystemExit(f"No rows found in {copied_csv}")

    summary = summarize(rows, args.gap_seconds, args.power_watts)
    dashboard_path = output_dir / f"recamera_runtime_dashboard_{stamp}.html"
    summary_path = output_dir / f"recamera_runtime_summary_{stamp}.md"

    dashboard_path.write_text(build_html(rows, summary, copied_csv.name))
    write_summary(summary, summary_path)

    print(f"CSV:       {copied_csv}")
    print(f"Dashboard: {dashboard_path}")
    print(f"Summary:   {summary_path}")
    print(
        "Result: "
        f"{fmt_minutes(summary['observed_seconds'])} min observed, "
        f"{fmt_minutes(summary['online_seconds'])} min online, "
        f"{summary['event_count']} target events, "
        f"{len(summary['offline_segments'])} offline/reboot gaps"
    )


if __name__ == "__main__":
    main()
