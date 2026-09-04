# Church Setup Guide

This guide applies once a PTZ Controller Mac release is available. The current repository contains a UI prototype only and cannot operate the camera yet.

## Bring to church

- Mac and charger
- Thrustmaster T.16000M FCS and its USB cable
- USB-C adapter or powered USB hub, if the Mac needs one
- Ethernet cable for the Mac
- Sony SRG-300SE camera IP address and camera login details

## Recommended physical connection

```text
Sony SRG-300SE -- Ethernet switch -- Mac
T.16000M FCS ---------------- USB -- Mac
```

Use Ethernet for the Mac whenever possible. Wi-Fi may work, but a wired connection is preferable for consistent live-control latency.

## Before opening the app

1. Power on the Sony camera and connect it to the church network.
2. Connect the Mac to the same network switch or VLAN.
3. Connect the T.16000M directly to the Mac, or to a powered hub.
4. In a web browser, open the camera's IP address and confirm it is reachable.
5. Confirm the camera is configured for VISCA over IP. The app will default to UDP port `52381`; use the actual configured port if it differs.

## Install the Mac app

1. Open this repository's **Releases** page on GitHub.
2. Download the latest macOS `.dmg`.
3. Open the `.dmg`, then drag **PTZ Controller** to **Applications**.
4. Open the app from Applications.

Early test builds may need explicit approval in **System Settings → Privacy & Security**. Signed and notarized releases are planned before the app is shared broadly.

## Connect and test safely

1. In PTZ Controller, enter the camera name, IP address, and UDP port.
2. Select **Connect**.
3. Set a low movement speed.
4. Test on-screen Pan Left, Stop, Pan Right, Stop, Tilt, and Zoom controls.
5. Do not continue until the on-screen Stop control reliably stops movement.

Testing manual controls first separates network/camera problems from joystick-mapping problems.

## Configure the joystick

1. Open **Calibration** and select the T.16000M.
2. Verify that X, Y, twist, throttle, hat switch, and button values change when used.
3. Center the stick and set the dead zone so the camera remains still when released.
4. Start with a low throttle speed cap.
5. Assign actions in the button-mapping screen.

Suggested first mapping:

| Physical control | Action |
| --- | --- |
| Stick X / Y | Pan / Tilt |
| Twist | Zoom |
| Throttle | Maximum Pan/Tilt speed |
| Button 1 | Preset 1: Pulpit |
| Button 2 | Preset 2: Piano |
| Button 3 | Preset 3: Worship Team |
| Button 4 | Preset 4: Wide Stage |
| Button 5 | Preset 5: Audience |
| Button 6 | One-push autofocus |
| Hat switch | Fine movement mode |

## First live test

Plan a 20–30 minute test when no service is running. Test each direction, Stop, zoom, each preset, and joystick reconnect behavior. Save the validated configuration as a named profile, such as `Sanctuary Sunday Service`.

Avoid storing or overwriting presets until recalls have been verified. The finished application will require a deliberate separate action for preset storage.
