# Demo Report: reCamera Pro Cat Detection to Meshtastic Alert

## Purpose

This pilot was built to validate whether a reCamera Pro can become an edge trigger for a Meshtastic field network.

The test uses stray cats in the company area as an accessible proxy target. In a field deployment, the same pattern could be adapted to notify researchers when a target species or risk event appears, such as a tiger, wolf, or potential poacher.

## Demo Chain

```text
cat appears
-> reCamera Pro detects target locally
-> trigger program validates the inference result
-> GPIO188 outputs a 3.3 V pulse for 3 seconds
-> Meshtastic transmitter detects the signal
-> alert is sent through the Meshtastic network
-> Wio Tracker L1 Pro receives the alert
```

## Camera-Side Behavior

- Target classes: `cat` and `person` during development.
- GPIO signal: Linux GPIO188, mapped to `CAN0_RXD_M0 / GPIO5_D4`.
- Pulse duration: 3 seconds.
- Cooldown: 60 seconds.
- Snapshot: one local JPG saved when the GPIO trigger happens.
- Snapshot retention: up to 1000 images, then remove the oldest 100.

## Evidence to Include

Add selected evidence here before publication:

| Evidence | Suggested File | Notes |
|---|---|---|
| Wiring photo | `images/wiring.jpg` | Show reCamera Pro, Meshtastic node, and GPIO connection |
| Trigger gallery | `images/trigger-gallery-sample.jpg` | Show several trigger snapshots or the generated HTML report |
| Receiver photo | `images/wio-tracker-alert.jpg` | Show Wio Tracker L1 Pro receiving an alert |
| Runtime chart | `images/runtime-dashboard.png` | Optional: show deployment uptime and trigger count |

Avoid publishing exact sensitive field coordinates or unreviewed wildlife images.

## Lessons Learned

- A simple GPIO pulse is an effective boundary between edge AI and radio networking.
- Keeping the camera-side detection logic separate from the Meshtastic node makes the chain easier to debug.
- Saving a snapshot at trigger time is important for distinguishing real events from false positives.
- A cooldown window is needed so one continuous appearance does not create repeated alerts.

## Next Steps

- Replace the proxy target with a field-relevant detection model.
- Define a Meshtastic alert payload format for species, confidence, timestamp, and device ID.
- Add power-budget testing for solar deployments.
- Document the receiver-side behavior for Wio Tracker L1 Pro.
- Review privacy and species-risk guidance before public field use.

