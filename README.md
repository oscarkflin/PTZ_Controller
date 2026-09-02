# PTZ Controller

A local desktop controller for a USB joystick and Sony SRG-300SE PTZ camera.

The application will be built with Tauri: a TypeScript desktop interface backed by Rust for joystick HID input and Sony VISCA-over-IP control. It will run locally on macOS and Windows, without OBS or cloud services.

## Status

Project foundation. The repository is intentionally prepared before application scaffolding because Rust is not installed on this Windows machine yet.

## Planned stack

- Desktop shell: Tauri 2
- Interface: Vanilla TypeScript, HTML, and CSS
- Controller core: Rust
- Camera protocol: Sony VISCA over UDP/IP
- Initial target: Sony SRG-300SE and Thrustmaster T.16000M FCS

## Development stages

1. Create the Tauri app shell and visual controller prototype.
2. Add a simulated camera and joystick so the UI can be verified on Windows.
3. Implement VISCA manual pan, tilt, zoom, and stop commands.
4. Verify camera control on the Mac and Sony SRG-300SE.
5. Add joystick detection, calibration, mapping, presets, and release automation.

See [the implementation plan](docs/IMPLEMENTATION_PLAN.md) for details.

## First-time setup

When development begins, install the current Rust toolchain, Node.js LTS, and the Windows C++ Build Tools, then scaffold the Tauri application in this repository. No camera or joystick configuration is required for the first UI prototype.

## Releases

GitHub Actions will eventually build Windows and macOS installers from version tags and attach them to GitHub Releases. macOS code signing and notarization will be added before broad distribution.
