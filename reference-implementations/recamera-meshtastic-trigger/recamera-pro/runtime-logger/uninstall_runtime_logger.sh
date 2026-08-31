#!/bin/sh
set -eu

if [ -x /etc/init.d/S98recamera_runtime_logger ]; then
    /etc/init.d/S98recamera_runtime_logger stop || true
fi

rm -f /etc/init.d/S98recamera_runtime_logger
rm -f /userdata/recamera_runtime_logger.py
rm -f /userdata/recamera_runtime_logger.conf
rm -f /userdata/export_runtime_report.py

echo "Runtime logger uninstalled."
echo "Kept data file: /userdata/recamera_runtime_monitor.csv"
