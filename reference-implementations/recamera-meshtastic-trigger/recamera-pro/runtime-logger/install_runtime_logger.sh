#!/bin/sh
set -eu

BASE_DIR=$(cd "$(dirname "$0")" && pwd)

cp "$BASE_DIR/recamera_runtime_logger.py" /userdata/recamera_runtime_logger.py
cp "$BASE_DIR/recamera_runtime_logger.conf" /userdata/recamera_runtime_logger.conf
cp "$BASE_DIR/export_runtime_report.py" /userdata/export_runtime_report.py
cp "$BASE_DIR/S98recamera_runtime_logger" /etc/init.d/S98recamera_runtime_logger

chmod 755 /userdata/recamera_runtime_logger.py
chmod 644 /userdata/recamera_runtime_logger.conf
chmod 755 /userdata/export_runtime_report.py
chmod 755 /etc/init.d/S98recamera_runtime_logger

/etc/init.d/S98recamera_runtime_logger restart

echo
echo "Installed reCamera runtime logger."
echo "Config: /userdata/recamera_runtime_logger.conf"
echo "CSV:    /userdata/recamera_runtime_monitor.csv"
echo "Log:    /userdata/recamera_runtime_logger.log"
echo
echo "Check status:"
echo "  /etc/init.d/S98recamera_runtime_logger status"
echo
echo "Watch CSV:"
echo "  tail -f /userdata/recamera_runtime_monitor.csv"
