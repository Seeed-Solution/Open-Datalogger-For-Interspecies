# Tools

These tools run from a computer, not from the Meshtastic node.

## Download Trigger Snapshots

```bash
python3 download_snapshots.py \
  --host <recamera-ip> \
  --user root \
  --latest 100 \
  --output-dir ./recamera_trigger_snapshots
```

## Generate Runtime Dashboard

```bash
python3 generate_runtime_dashboard.py \
  --host <recamera-ip> \
  --user root
```

The dashboard summarizes online time, offline gaps, trigger events, and estimated energy use.

