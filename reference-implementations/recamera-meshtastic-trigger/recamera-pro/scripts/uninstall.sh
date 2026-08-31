#!/bin/sh
set -eu

if [ -x /etc/init.d/S99recamera_gpio_trigger ]; then
    /etc/init.d/S99recamera_gpio_trigger stop || true
fi

rm -f /etc/init.d/S99recamera_gpio_trigger
rm -f /userdata/person_gpio_trigger.py
rm -f /userdata/recamera_trigger.conf
rm -f /userdata/recamera_gpio_trigger.log
rm -f /var/run/recamera_gpio_trigger.pid

echo "Uninstalled reCamera GPIO trigger."
