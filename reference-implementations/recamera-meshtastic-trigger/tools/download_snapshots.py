#!/usr/bin/env python3
import argparse
import shlex
import subprocess
from pathlib import Path


DEFAULT_REMOTE_DIR = "/mnt/rc_mmcblk0p8/recamera_trigger_snapshots"


def run(command):
    subprocess.run(command, check=True)


def output(command):
    return subprocess.check_output(command, text=True)


def wrap_sshpass(command, enabled):
    if enabled:
        return ["sshpass", "-e"] + command
    return command


def list_remote_files(args):
    remote_command = (
        f"(ls -1t {shlex.quote(args.remote_dir)}/*.jpg "
        f"{shlex.quote(args.remote_dir)}/*.jpeg 2>/dev/null || true) | head -n {args.latest}"
    )
    command = wrap_sshpass(
        [
            "ssh",
            "-o",
            "StrictHostKeyChecking=no",
            "-o",
            "UserKnownHostsFile=/dev/null",
            f"{args.user}@{args.host}",
            remote_command,
        ],
        args.use_sshpass_env,
    )
    raw = output(command)
    return [line.strip() for line in raw.splitlines() if line.strip()]


def download_files(args, files):
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for remote_path in files:
        remote = f"{args.user}@{args.host}:{remote_path}"
        command = wrap_sshpass(
            [
                "scp",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                remote,
                str(output_dir / Path(remote_path).name),
            ],
            args.use_sshpass_env,
        )
        run(command)
    return output_dir


def parse_args():
    parser = argparse.ArgumentParser(
        description="Download recent trigger snapshots from reCamera Pro."
    )
    parser.add_argument("--host", required=True, help="reCamera IP or hostname.")
    parser.add_argument("--user", default="root", help="SSH username. Default: root.")
    parser.add_argument("--latest", type=int, default=100, help="How many recent photos to download.")
    parser.add_argument(
        "--remote-dir",
        default=DEFAULT_REMOTE_DIR,
        help=f"Remote snapshot directory. Default: {DEFAULT_REMOTE_DIR}",
    )
    parser.add_argument(
        "--output-dir",
        default="recamera_trigger_snapshots",
        help="Local output directory.",
    )
    parser.add_argument(
        "--use-sshpass-env",
        action="store_true",
        help="Wrap ssh/scp with sshpass -e. Set SSHPASS to the SSH password first.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    files = list_remote_files(args)
    if not files:
        print("No snapshots found.")
        return
    output_dir = download_files(args, files)
    print(f"Downloaded {len(files)} snapshots to {output_dir}")


if __name__ == "__main__":
    main()
