#!/usr/bin/env python3
import asyncio
import csv
import json
import os
import shutil
import ssl
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import websockets


DEFAULT_CONFIG = "/userdata/recamera_runtime_logger.conf"

CSV_FIELDS = [
    "timestamp_iso",
    "row_type",
    "boot_id",
    "uptime_seconds",
    "estimated_energy_wh",
    "estimated_battery_used_pct",
    "inference_status",
    "inference_actual_fps",
    "root_free_mb",
    "userdata_free_mb",
    "frames_seen",
    "detections_seen",
    "target_classes_seen",
    "target_seen_count",
    "target_max_score",
    "target_last_class",
    "target_last_score",
    "event_class",
    "event_score",
    "event_action",
    "event_cooldown_seconds",
    "gpio_expected",
    "gpio_pulse_seconds",
    "note",
]


def utc_now_iso():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def load_config(path):
    config = {
        "LOG_CSV": "/userdata/recamera_runtime_monitor.csv",
        "HEARTBEAT_INTERVAL_SECONDS": "60",
        "TARGET_CLASSES": "cat",
        "MIN_SCORE": "0.5",
        "EVENT_COOLDOWN_SECONDS": "10",
        "POWER_WATTS": "5.6",
        "BATTERY_WH": "385",
        "GPIO_EXPECTED": "188",
        "GPIO_PULSE_SECONDS": "3",
        "WS_URI": "wss://127.0.0.1/ws/inference/results",
        "API_KEY": "",
    }

    cfg_path = Path(path)
    if cfg_path.exists():
        for raw_line in cfg_path.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            config[key.strip()] = value.strip().strip('"').strip("'")
    return config


def parse_target_classes(config):
    raw_value = config.get("TARGET_CLASSES") or "cat"
    targets = [item.strip() for item in raw_value.split(",") if item.strip()]
    return set(targets or ["person"])


def read_api_key(ssl_ctx):
    url = "https://127.0.0.1/cgi-bin/entry.cgi/web/setting"
    data = urllib.request.urlopen(url, context=ssl_ctx, timeout=5).read()
    return json.loads(data.decode("utf-8"))["sApiKey"]


def read_json_url(url, ssl_ctx, api_key="", timeout=3):
    try:
        request = urllib.request.Request(url)
        if api_key:
            request.add_header("Authorization", f"Bearer {api_key}")
        data = urllib.request.urlopen(request, context=ssl_ctx, timeout=timeout).read()
        return json.loads(data.decode("utf-8"))
    except Exception:
        return {}


def read_text(path, default=""):
    try:
        return Path(path).read_text().strip()
    except Exception:
        return default


def read_uptime_seconds():
    raw = read_text("/proc/uptime", "0")
    try:
        return float(raw.split()[0])
    except Exception:
        return 0.0


def free_mb(path):
    try:
        usage = shutil.disk_usage(path)
        return round(usage.free / 1024 / 1024, 1)
    except Exception:
        return ""


def detection_entries(payload):
    detection = payload.get("detection") or payload.get("data", {}).get("detection", {})
    return detection.get("entries", [])


def best_target(entries, target_classes, min_score):
    matches = []
    for entry in entries:
        class_name = entry.get("class_name")
        score = float(entry.get("score", 0) or 0)
        if class_name in target_classes and score >= min_score:
            matches.append(entry)
    if not matches:
        return None
    return max(matches, key=lambda item: float(item.get("score", 0) or 0))


class CsvLog:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists() or self.path.stat().st_size == 0:
            with self.path.open("w", newline="") as handle:
                csv.DictWriter(handle, fieldnames=CSV_FIELDS).writeheader()

    def append(self, row):
        full_row = {field: row.get(field, "") for field in CSV_FIELDS}
        with self.path.open("a", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
            writer.writerow(full_row)


class WindowStats:
    def __init__(self):
        self.reset()

    def reset(self):
        self.frames_seen = 0
        self.detections_seen = 0
        self.target_seen_count = 0
        self.target_classes_seen = set()
        self.target_max_score = 0.0
        self.target_last_class = ""
        self.target_last_score = 0.0

    def record_payload(self, entries, target_classes, min_score):
        self.frames_seen += 1
        self.detections_seen += len(entries)
        target = best_target(entries, target_classes, min_score)
        if not target:
            return None

        score = float(target.get("score", 0) or 0)
        class_name = target.get("class_name", "")
        self.target_seen_count += 1
        self.target_classes_seen.add(class_name)
        self.target_max_score = max(self.target_max_score, score)
        self.target_last_class = class_name
        self.target_last_score = score
        return target


class RuntimeLogger:
    def __init__(self, config):
        self.config = config
        self.target_classes = parse_target_classes(config)
        self.min_score = float(config["MIN_SCORE"])
        self.heartbeat_interval = float(config["HEARTBEAT_INTERVAL_SECONDS"])
        self.event_cooldown = float(config["EVENT_COOLDOWN_SECONDS"])
        self.power_watts = float(config["POWER_WATTS"])
        self.battery_wh = float(config["BATTERY_WH"])
        self.gpio_expected = config["GPIO_EXPECTED"]
        self.gpio_pulse_seconds = config["GPIO_PULSE_SECONDS"]
        self.ssl_ctx = ssl._create_unverified_context()
        self.api_key = config.get("API_KEY") or read_api_key(self.ssl_ctx)
        self.csv_log = CsvLog(config["LOG_CSV"])
        self.stats = WindowStats()
        self.last_event_monotonic = 0.0
        self.boot_id = read_text("/proc/sys/kernel/random/boot_id", "unknown")

    def common_row(self, row_type, note=""):
        uptime = read_uptime_seconds()
        energy_wh = uptime / 3600.0 * self.power_watts
        battery_pct = energy_wh / self.battery_wh * 100.0 if self.battery_wh > 0 else 0.0
        inference = read_json_url(
            "https://127.0.0.1/cgi-bin/entry.cgi/model/inference?id=0",
            self.ssl_ctx,
            self.api_key,
        )

        return {
            "timestamp_iso": utc_now_iso(),
            "row_type": row_type,
            "boot_id": self.boot_id,
            "uptime_seconds": round(uptime, 1),
            "estimated_energy_wh": round(energy_wh, 3),
            "estimated_battery_used_pct": round(battery_pct, 3),
            "inference_status": inference.get("sStatus", ""),
            "inference_actual_fps": inference.get("iActualFPS", ""),
            "root_free_mb": free_mb("/"),
            "userdata_free_mb": free_mb("/userdata"),
            "gpio_expected": self.gpio_expected,
            "gpio_pulse_seconds": self.gpio_pulse_seconds,
            "note": note,
        }

    def append_heartbeat(self):
        row = self.common_row("heartbeat")
        row.update(
            {
                "frames_seen": self.stats.frames_seen,
                "detections_seen": self.stats.detections_seen,
                "target_classes_seen": "|".join(sorted(self.stats.target_classes_seen)),
                "target_seen_count": self.stats.target_seen_count,
                "target_max_score": round(self.stats.target_max_score, 3),
                "target_last_class": self.stats.target_last_class,
                "target_last_score": round(self.stats.target_last_score, 3)
                if self.stats.target_last_score
                else "",
            }
        )
        self.csv_log.append(row)
        print(
            f"heartbeat frames={self.stats.frames_seen} "
            f"targets={self.stats.target_seen_count} "
            f"classes={row['target_classes_seen']}",
            flush=True,
        )
        self.stats.reset()

    def append_target_event(self, target):
        score = float(target.get("score", 0) or 0)
        class_name = target.get("class_name", "")
        row = self.common_row("target_event")
        row.update(
            {
                "event_class": class_name,
                "event_score": round(score, 3),
                "event_action": "would_trigger_gpio",
                "event_cooldown_seconds": self.event_cooldown,
            }
        )
        self.csv_log.append(row)
        print(
            f"target_event class={class_name} score={score:.2f} "
            f"expected_gpio={self.gpio_expected}",
            flush=True,
        )

    async def heartbeat_loop(self):
        while True:
            await asyncio.sleep(self.heartbeat_interval)
            self.append_heartbeat()

    async def websocket_loop(self):
        headers = {"Authorization": f"Bearer {self.api_key}"}

        while True:
            try:
                async with websockets.connect(
                    self.config["WS_URI"],
                    extra_headers=headers,
                    ssl=self.ssl_ctx,
                    ping_interval=20,
                    ping_timeout=20,
                ) as ws:
                    print(
                        "listening for runtime inference events: "
                        f"classes={','.join(sorted(self.target_classes))}, "
                        f"score>={self.min_score}",
                        flush=True,
                    )
                    async for raw in ws:
                        try:
                            payload = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        entries = detection_entries(payload)
                        target = self.stats.record_payload(
                            entries,
                            self.target_classes,
                            self.min_score,
                        )
                        if not target:
                            continue

                        now = time.monotonic()
                        if now - self.last_event_monotonic < self.event_cooldown:
                            continue

                        self.append_target_event(target)
                        self.last_event_monotonic = now
            except Exception as exc:
                print(f"runtime logger connection/error: {exc}; retrying in 3s", flush=True)
                await asyncio.sleep(3)

    async def run(self):
        self.csv_log.append(self.common_row("service_start", "runtime logger started"))
        await asyncio.gather(self.heartbeat_loop(), self.websocket_loop())


async def main():
    config_path = os.environ.get("RECAMERA_RUNTIME_LOGGER_CONFIG", DEFAULT_CONFIG)
    logger = RuntimeLogger(load_config(config_path))
    await logger.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("stopping runtime logger", flush=True)
