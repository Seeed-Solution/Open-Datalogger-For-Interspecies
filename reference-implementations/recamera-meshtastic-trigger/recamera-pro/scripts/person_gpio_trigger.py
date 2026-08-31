#!/usr/bin/env python3
import asyncio
import csv
import json
import os
import shutil
import ssl
import subprocess
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import websockets


DEFAULT_CONFIG = "/userdata/recamera_trigger.conf"


def load_config(path):
    config = {
        "GPIO": "188",
        "TARGET_CLASS": "person",
        "TARGET_CLASSES": "",
        "MIN_SCORE": "0.5",
        "PULSE_SECONDS": "3",
        "COOLDOWN_SECONDS": "60",
        "WS_URI": "wss://127.0.0.1/ws/inference/results",
        "API_KEY": "",
        "SAVE_SNAPSHOT": "1",
        "SNAPSHOT_DIR": "/mnt/rc_mmcblk0p8/recamera_trigger_snapshots",
        "SNAPSHOT_EVENT_CSV": "/mnt/rc_mmcblk0p8/recamera_trigger_snapshots/trigger_events.csv",
        "SNAPSHOT_MAX_FILES": "1000",
        "SNAPSHOT_DELETE_BATCH": "100",
        "SNAPSHOT_MIN_FREE_MB": "1024",
        "SNAPSHOT_COMPRESS": "1",
        "SNAPSHOT_FFMPEG_Q": "5",
        "SNAPSHOT_TARGET_KB": "500",
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


def read_api_key(ssl_ctx):
    url = "https://127.0.0.1/cgi-bin/entry.cgi/web/setting"
    data = urllib.request.urlopen(url, context=ssl_ctx, timeout=5).read()
    return json.loads(data.decode("utf-8"))["sApiKey"]


def bool_config(value):
    return str(value).strip().lower() in ("1", "true", "yes", "on")


class GpioOutput:
    def __init__(self, gpio):
        self.gpio = int(gpio)
        self.path = Path(f"/sys/class/gpio/gpio{self.gpio}")

    def write_file(self, path, value):
        Path(path).write_text(str(value))

    def setup(self):
        if not self.path.exists():
            self.write_file("/sys/class/gpio/export", self.gpio)
            time.sleep(0.2)
        self.write_file(self.path / "direction", "out")
        self.low()

    def high(self):
        self.write_file(self.path / "value", "1")

    def low(self):
        self.write_file(self.path / "value", "0")


class SnapshotCapture:
    def __init__(self, config, ssl_ctx, api_key):
        self.enabled = bool_config(config.get("SAVE_SNAPSHOT", "0"))
        self.output_dir = Path(config["SNAPSHOT_DIR"])
        self.event_csv = Path(config["SNAPSHOT_EVENT_CSV"])
        self.max_files = int(config["SNAPSHOT_MAX_FILES"])
        self.delete_batch = int(config["SNAPSHOT_DELETE_BATCH"])
        self.min_free_mb = float(config["SNAPSHOT_MIN_FREE_MB"])
        self.compress = bool_config(config.get("SNAPSHOT_COMPRESS", "0"))
        self.ffmpeg_q = int(config["SNAPSHOT_FFMPEG_Q"])
        self.target_bytes = int(float(config.get("SNAPSHOT_TARGET_KB", "0")) * 1024)
        self.ssl_ctx = ssl_ctx
        self.api_key = api_key

    def request_json(self, path, data=None, timeout=8):
        url = f"https://127.0.0.1/cgi-bin/entry.cgi{path}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        body = None
        method = "GET"
        if data is not None:
            headers["Content-Type"] = "application/json"
            body = json.dumps(data).encode("utf-8")
            method = "POST"
        request = urllib.request.Request(url, data=body, headers=headers, method=method)
        response = urllib.request.urlopen(request, context=self.ssl_ctx, timeout=timeout)
        return json.loads(response.read().decode("utf-8"))

    def free_mb(self):
        usage = shutil.disk_usage(self.output_dir)
        return usage.free / 1024 / 1024

    def snapshot_files(self):
        if not self.output_dir.exists():
            return []
        files = []
        for path in self.output_dir.iterdir():
            if path.is_file() and path.suffix.lower() in (".jpg", ".jpeg"):
                files.append(path)
        return sorted(files, key=lambda path: path.stat().st_mtime)

    def rotate_if_needed(self):
        files = self.snapshot_files()
        if len(files) < self.max_files:
            return 0
        remove_count = max(1, min(self.delete_batch, len(files)))
        removed = 0
        for path in files[:remove_count]:
            try:
                path.unlink()
                removed += 1
            except Exception as exc:
                print(f"snapshot cleanup failed for {path}: {exc}", flush=True)
        return removed

    def make_filename(self, class_name, score, gpio):
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_class = "".join(ch if ch.isalnum() else "_" for ch in class_name)
        return f"{stamp}_{safe_class}_{score:.2f}_gpio{gpio}.jpg"

    def wait_for_capture(self, capture_id, timeout_seconds=8):
        deadline = time.monotonic() + timeout_seconds
        last_capture = {}
        while time.monotonic() < deadline:
            status = self.request_json("/record/capture/status", timeout=5)
            last_capture = status.get("dLastCapture") or {}
            if last_capture.get("sID") == capture_id:
                state = last_capture.get("sStatus")
                if state in ("COMPLETED", "FAILED", "INTERRUPTED", "CANCELED"):
                    return last_capture
            time.sleep(0.4)
        return last_capture

    def compress_image(self, source_path, final_path):
        if not self.compress or not shutil.which("ffmpeg"):
            source_path.rename(final_path)
            return final_path

        qualities = []
        for quality in (self.ffmpeg_q, 7, 9, 11, 13, 16, 20):
            if quality not in qualities:
                qualities.append(quality)
        best_tmp = None
        try:
            for quality in qualities:
                tmp_path = final_path.with_suffix(f".q{quality}.tmp.jpg")
                subprocess.run(
                    [
                        "ffmpeg",
                        "-y",
                        "-hide_banner",
                        "-loglevel",
                        "error",
                        "-i",
                        str(source_path),
                        "-q:v",
                        str(quality),
                        str(tmp_path),
                    ],
                    check=True,
                    timeout=15,
                )
                if best_tmp and best_tmp.exists():
                    best_tmp.unlink()
                best_tmp = tmp_path
                if not self.target_bytes or tmp_path.stat().st_size <= self.target_bytes:
                    break
            source_path.unlink(missing_ok=True)
            best_tmp.rename(final_path)
        except Exception as exc:
            print(f"snapshot compression failed: {exc}; keeping original", flush=True)
            for tmp_path in final_path.parent.glob(f"{final_path.stem}.q*.tmp.jpg"):
                tmp_path.unlink(missing_ok=True)
            source_path.rename(final_path)
        return final_path

    def write_event(self, class_name, score, gpio, snapshot_path, status, note=""):
        self.event_csv.parent.mkdir(parents=True, exist_ok=True)
        is_new = not self.event_csv.exists() or self.event_csv.stat().st_size == 0
        fields = [
            "timestamp_iso",
            "class_name",
            "score",
            "gpio",
            "snapshot_path",
            "snapshot_status",
            "snapshot_size_bytes",
            "note",
        ]
        with self.event_csv.open("a", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            if is_new:
                writer.writeheader()
            size = ""
            if snapshot_path:
                try:
                    size = Path(snapshot_path).stat().st_size
                except Exception:
                    size = ""
            writer.writerow(
                {
                    "timestamp_iso": datetime.now().astimezone().isoformat(timespec="seconds"),
                    "class_name": class_name,
                    "score": f"{score:.3f}",
                    "gpio": gpio,
                    "snapshot_path": snapshot_path,
                    "snapshot_status": status,
                    "snapshot_size_bytes": size,
                    "note": note,
                }
            )

    def capture(self, class_name, score, gpio):
        if not self.enabled:
            return ""
        if not str(self.output_dir).startswith("/mnt/"):
            note = f"SNAPSHOT_DIR must start with /mnt/: {self.output_dir}"
            print(note, flush=True)
            self.write_event(class_name, score, gpio, "", "SKIPPED", note)
            return ""

        self.output_dir.mkdir(parents=True, exist_ok=True)
        free_mb = self.free_mb()
        if free_mb < self.min_free_mb:
            note = f"free space too low: {free_mb:.1f}MB < {self.min_free_mb:.1f}MB"
            print(f"snapshot skipped: {note}", flush=True)
            self.write_event(class_name, score, gpio, "", "SKIPPED", note)
            return ""

        removed = self.rotate_if_needed()
        if removed:
            print(f"snapshot cleanup: removed oldest {removed} files", flush=True)

        response = self.request_json(
            "/record/capture/start",
            {"sOutput": str(self.output_dir), "sFormat": "JPG"},
            timeout=8,
        )
        capture = response.get("dCapture") or {}
        capture_id = capture.get("sID", "")
        if not capture_id:
            note = f"capture start response: {response}"
            print(f"snapshot failed: {note}", flush=True)
            self.write_event(class_name, score, gpio, "", "FAILED", note)
            return ""

        capture = self.wait_for_capture(capture_id)
        status = capture.get("sStatus", "UNKNOWN")
        source_path = Path(capture.get("sOutputDirectory", self.output_dir)) / capture.get("sFileName", "")
        if status != "COMPLETED" or not source_path.exists():
            note = f"capture status={status}, source={source_path}"
            print(f"snapshot failed: {note}", flush=True)
            self.write_event(class_name, score, gpio, "", status, note)
            return ""

        final_path = self.output_dir / self.make_filename(class_name, score, gpio)
        final_path = self.compress_image(source_path, final_path)
        self.write_event(class_name, score, gpio, str(final_path), "COMPLETED")
        print(f"snapshot saved: {final_path}", flush=True)
        return str(final_path)


def detection_entries(payload):
    detection = payload.get("detection") or payload.get("data", {}).get("detection", {})
    return detection.get("entries", [])


def parse_target_classes(config):
    raw_value = config.get("TARGET_CLASSES") or config.get("TARGET_CLASS") or "person"
    targets = [item.strip() for item in raw_value.split(",") if item.strip()]
    return set(targets or ["person"])


def best_target(payload, target_classes, min_score):
    matches = []
    for entry in detection_entries(payload):
        score = float(entry.get("score", 0) or 0)
        if entry.get("class_name") in target_classes and score >= min_score:
            matches.append(entry)
    if not matches:
        return None
    return max(matches, key=lambda item: float(item.get("score", 0) or 0))


async def main():
    config_path = os.environ.get("RECAMERA_TRIGGER_CONFIG", DEFAULT_CONFIG)
    config = load_config(config_path)

    gpio = GpioOutput(config["GPIO"])
    target_classes = parse_target_classes(config)
    min_score = float(config["MIN_SCORE"])
    pulse_seconds = float(config["PULSE_SECONDS"])
    cooldown_seconds = float(config["COOLDOWN_SECONDS"])
    ws_uri = config["WS_URI"]

    ssl_ctx = ssl._create_unverified_context()
    api_key = config.get("API_KEY") or read_api_key(ssl_ctx)
    headers = {"Authorization": f"Bearer {api_key}"}
    snapshot = SnapshotCapture(config, ssl_ctx, api_key)
    last_trigger = 0.0

    print(f"initializing gpio{gpio.gpio}=0", flush=True)
    gpio.setup()
    print(
        f"listening: classes={','.join(sorted(target_classes))}, score>={min_score}, "
        f"pulse gpio{gpio.gpio} for {pulse_seconds:g}s, cooldown {cooldown_seconds:g}s",
        flush=True,
    )
    if snapshot.enabled:
        print(
            f"snapshots: dir={snapshot.output_dir}, max={snapshot.max_files}, "
            f"delete_batch={snapshot.delete_batch}, compress={snapshot.compress}, "
            f"target_kb={snapshot.target_bytes // 1024 if snapshot.target_bytes else 0}",
            flush=True,
        )

    while True:
        try:
            async with websockets.connect(
                ws_uri,
                extra_headers=headers,
                ssl=ssl_ctx,
                ping_interval=20,
                ping_timeout=20,
            ) as ws:
                async for raw in ws:
                    try:
                        payload = json.loads(raw)
                    except json.JSONDecodeError:
                        continue

                    target = best_target(payload, target_classes, min_score)
                    if not target:
                        continue

                    now = time.monotonic()
                    remaining = cooldown_seconds - (now - last_trigger)
                    score = float(target.get("score", 0) or 0)
                    class_name = target.get("class_name", "unknown")
                    if remaining > 0:
                        print(
                            f"{class_name} ignored during cooldown: "
                            f"score={score:.2f}, wait {remaining:.1f}s",
                            flush=True,
                        )
                        continue

                    print(
                        f"TRIGGER {class_name} score={score:.2f}: "
                        f"gpio{gpio.gpio}=1 for {pulse_seconds:g}s",
                        flush=True,
                    )
                    loop = asyncio.get_running_loop()
                    snapshot_future = loop.run_in_executor(
                        None,
                        snapshot.capture,
                        class_name,
                        score,
                        gpio.gpio,
                    )
                    gpio.high()
                    await asyncio.sleep(pulse_seconds)
                    gpio.low()
                    last_trigger = time.monotonic()
                    snapshot_path = await snapshot_future
                    print(
                        f"pulse done: gpio{gpio.gpio}=0"
                        + (f", snapshot={snapshot_path}" if snapshot_path else ""),
                        flush=True,
                    )
        except Exception as exc:
            print(f"connection/error: {exc}; retrying in 3s", flush=True)
            try:
                gpio.low()
            except Exception as gpio_exc:
                print(f"failed to force gpio low: {gpio_exc}", flush=True)
            await asyncio.sleep(3)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("stopping", flush=True)
