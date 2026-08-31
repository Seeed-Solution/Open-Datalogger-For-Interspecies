#!/bin/sh
set -eu

GPIO="${1:-188}"
GPIO_PATH="/sys/class/gpio/gpio${GPIO}"

if [ ! -d "$GPIO_PATH" ]; then
    echo "$GPIO" > /sys/class/gpio/export
    sleep 0.2
fi

echo out > "$GPIO_PATH/direction"
echo 0 > "$GPIO_PATH/value"

echo "GPIO${GPIO} toggle test started."
echo "Measure GPIO${GPIO} against GND. It will switch every 5 seconds."
echo "Press Ctrl-C to stop; the script will pull GPIO${GPIO} low before exit."

trap 'echo 0 > "$GPIO_PATH/value"; echo; echo "GPIO${GPIO}=0, stopped"; exit 0' INT TERM EXIT

while true; do
    echo 1 > "$GPIO_PATH/value"
    date "+%H:%M:%S GPIO${GPIO}=1"
    sleep 5
    echo 0 > "$GPIO_PATH/value"
    date "+%H:%M:%S GPIO${GPIO}=0"
    sleep 5
done
