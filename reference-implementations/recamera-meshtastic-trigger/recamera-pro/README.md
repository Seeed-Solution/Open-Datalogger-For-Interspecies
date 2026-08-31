# reCamera Pro Setup

These files run on the reCamera Pro. They read the local AI inference stream and output a GPIO pulse when a configured target class is detected.

## Files

```text
scripts/
  person_gpio_trigger.py      main trigger service
  recamera_trigger.conf       trigger configuration
  S99recamera_gpio_trigger    init script
  install.sh                  install service on the camera
  uninstall.sh                remove service from the camera
  test_gpio_toggle.sh         manual GPIO pulse test

runtime-logger/
  recamera_runtime_logger.py  optional heartbeat and target-event logger
  recamera_runtime_logger.conf
  S98recamera_runtime_logger
  install_runtime_logger.sh
  uninstall_runtime_logger.sh
```

## Installation Shape

Copy the scripts to the camera, SSH into the camera, then run:

```bash
cd /userdata/recamera_gpio_trigger
sh install.sh
```

The installed service reads:

```text
/userdata/recamera_trigger.conf
```

The default demo configuration is:

```ini
GPIO=188
TARGET_CLASSES=cat
MIN_SCORE=0.10
PULSE_SECONDS=3
COOLDOWN_SECONDS=60
SAVE_SNAPSHOT=1
SNAPSHOT_TARGET_KB=500
SNAPSHOT_MAX_FILES=1000
SNAPSHOT_DELETE_BATCH=100
```

For lab testing, you can temporarily set `TARGET_CLASSES=person,cat`. For the public demo, keep the default focused on `cat`.

## Trigger Output

The service sets GPIO188 high for 3 seconds, then returns it to low. It will not trigger again during the 60-second cooldown window.

Snapshots are saved on the camera under:

```text
/mnt/rc_mmcblk0p8/recamera_trigger_snapshots
```

Use `tools/download_snapshots.py` from a computer to download the latest photos.
