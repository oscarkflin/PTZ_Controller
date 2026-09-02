# Implementation Plan

## Goal

Create a standalone, local PTZ controller that maps a Thrustmaster T.16000M FCS joystick to a Sony SRG-300SE camera using VISCA over IP.

## Architecture

```text
T.16000M USB joystick
        |
        v
Rust HID service -> normalized JoystickState -> mapping engine -> PTZIntent
                                                               |
                                                               v
                                                    VISCA UDP client
                                                               |
                                                               v
                                                    Sony SRG-300SE

Tauri interface: configuration, debug values, manual controls, presets
```

## Milestone 1: Windows UI prototype

- Scaffold a Tauri 2 app with Vanilla TypeScript.
- Build the main controller layout, connection controls, camera test pad, joystick monitor, and presets.
- Add simulated camera state and simulated joystick input.
- Verify the interface without camera hardware.

## Milestone 2: Camera connectivity

- Add editable camera IP address and UDP port (default `52381`).
- Implement VISCA packet framing and sequence handling for the SRG-300SE.
- Add manual pan, tilt, zoom, and stop commands.
- Test against the physical camera before enabling joystick-driven commands.

## Milestone 3: Joystick input and mapping

- Enumerate HID joysticks and display raw axes/buttons.
- Record actual T.16000M controls on macOS and Windows.
- Normalize inputs, configure calibration/dead zone, and add a response curve.
- Map X/Y to proportional pan/tilt; twist to zoom; throttle to PTZ speed cap.

## Milestone 4: Operator safety and workflow

- Send Stop on disconnect, stale input, loss of connection, and application shutdown.
- Add preset recall and a deliberate preset-store flow.
- Persist camera, joystick, and mapping profiles locally.
- Add reconnect behavior and clear connection status.

## Milestone 5: Distribution

- Add tests for mapping and VISCA packet generation.
- Add GitHub Actions CI for Windows and macOS builds.
- Publish installers to GitHub Releases from version tags.
- Add macOS signing/notarization before sharing outside the team.

## Decisions already made

- Use a local desktop application, not a browser-hosted website.
- Use Tauri for a web-style UI packaged as a native desktop executable.
- Keep hardware/protocol logic in Rust and independent of the UI.
- Treat macOS hardware testing as the source of truth; Windows initially verifies the UI and simulated behavior.
