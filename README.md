# PTZ Controller

Local desktop control for a USB joystick and Sony SRG-300SE PTZ camera.

PTZ Controller will be a standalone macOS and Windows application. It will connect a Thrustmaster T.16000M FCS joystick to a Sony camera on the local network; it does not require OBS, a cloud account, or an Internet connection during use.

> **Current status:** interactive UI prototype only. It does not yet control a real camera or joystick, and no installable release exists yet.

## What the finished app will do

- Connect to a Sony SRG-300SE using VISCA over UDP/IP.
- Use on-screen Pan, Tilt, Zoom, and Stop controls.
- Read joystick axes and buttons.
- Provide proportional pan/tilt, variable zoom, dead-zone calibration, and a response curve.
- Recall camera presets from configurable joystick buttons.
- Save camera and joystick mapping profiles locally.
- Stop camera movement when the joystick disconnects, app closes, or input becomes stale.

## Planned technology

- **Desktop app:** Tauri 2
- **User interface:** Vanilla TypeScript, HTML, and CSS
- **Hardware and camera layer:** Rust
- **Camera protocol:** Sony VISCA over UDP/IP; default port `52381`, configurable per camera

## Try the UI prototype now

The working interface mock-up is in [`ui-prototype/`](ui-prototype/). It intentionally simulates camera and joystick activity, so it is safe to explore without hardware.

Open [`ui-prototype/index.html`](ui-prototype/index.html) in a browser, or serve that directory locally with a static web server. The production application will package the same interface in a normal desktop window.

## Church setup (when the first real release is available)

The concise field checklist is in [docs/CHURCH_SETUP.md](docs/CHURCH_SETUP.md). In short:

1. Connect the Mac and camera to the same Ethernet network.
2. Connect the T.16000M to the Mac over USB.
3. Confirm the camera’s IP address and VISCA-over-IP setting.
4. Install the Mac `.dmg` from the GitHub **Releases** page.
5. Test manual on-screen controls before mapping or moving by joystick.
6. Calibrate and assign joystick controls; then save the profile.

## Development roadmap

See [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) for the staged technical plan, including the Windows UI prototype, Mac hardware validation, safety controls, and release automation.

## Releases

When the production Tauri application is ready, GitHub Actions will build Windows and macOS installers from version tags and attach them to GitHub Releases. The release process and macOS signing notes are documented in [docs/RELEASING.md](docs/RELEASING.md).

For local Windows, macOS, and future GitHub Actions build steps, see [docs/BUILDING.md](docs/BUILDING.md).

## Repository

GitHub: <https://github.com/oscarkflin/PTZ_Controller>
