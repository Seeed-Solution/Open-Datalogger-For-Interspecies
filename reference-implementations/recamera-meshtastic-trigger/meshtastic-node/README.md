# Meshtastic Node Setup

This demo uses a Wio SX1262 with XIAO ESP32S3 as the transmitter node and a Wio Tracker L1 Pro as the receiver.

## Firmware

Flash both nodes with Meshtastic firmware using the official web flasher:

- <https://flash.meshtastic.org/>

Use a data-capable USB cable and a Chrome or Edge browser. Select the correct target device, choose a stable firmware release, and flash the node.

## Channel

Create or select a shared Meshtastic channel for the demo. The transmitter and receiver must use compatible channel settings.

Do not publish the channel pre-shared key. If you share screenshots, redact the key.

## Detection Sensor Module

On the transmitter node:

```text
Module Config
-> Detection Sensor
-> Enabled: on
-> Friendly Name: Cat
-> Monitor Pin: the GPIO connected to reCamera GPIO188
-> Detection Triggered Type: LOGIC_HIGH
```

The module sends a message when the monitored pin sees the configured trigger state. In this demo, the camera outputs a 3.3 V high pulse when the target is detected, so the Meshtastic trigger type is `LOGIC_HIGH`.

## Expected Result

When the camera detects the configured target class, the receiver should display a message similar to:

```text
Cat detected
```

