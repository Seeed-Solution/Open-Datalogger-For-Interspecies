#!/bin/sh
set -eu

BASE_DIR=$(cd "$(dirname "$0")" && pwd)

cp "$BASE_DIR/person_gpio_trigger.py" /userdata/person_gpio_trigger.py
cp "$BASE_DIR/recamera_trigger.conf" /userdata/recamera_trigger.conf
cp "$BASE_DIR/S99recamera_gpio_trigger" /etc/init.d/S99recamera_gpio_trigger

chmod 755 /userdata/person_gpio_trigger.py
chmod 644 /userdata/recamera_trigger.conf
chmod 755 /etc/init.d/S99recamera_gpio_trigger

/etc/init.d/S99recamera_gpio_trigger restart

echo
echo "Installed reCamera GPIO trigger."
echo "Config: /userdata/recamera_trigger.conf"
echo "Log:    /userdata/recamera_gpio_trigger.log"
echo
echo "Check status:"
echo "  /etc/init.d/S99recamera_gpio_trigger status"
echo
echo "Watch log:"
echo "  tail -f /userdata/recamera_gpio_trigger.log"
