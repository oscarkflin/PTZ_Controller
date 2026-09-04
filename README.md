# PTZ Controller

A local USB-joystick controller for the Sony SRG-300SE PTZ camera.

The first usable version is intentionally simple: a Python desktop application using the standard Tkinter UI toolkit, `pygame` for joystick input, and UDP VISCA-over-IP commands. It needs no OBS, cloud service, or Internet connection during normal operation.

## Current MVP

The Python controller now includes:

- Camera IP and UDP port configuration (`52381` default)
- Guarded **live command** mode, off by default
- Manual Pan, Tilt, Zoom, and Stop controls
- Preset recall buttons and confirmation-protected preset storage
- USB joystick scanning and live axis monitor
- Configurable dead zone and throttle-based movement speed
- Stop command on application close or joystick-control disable
- VISCA command packet tests

> The MVP has not yet been verified against the physical Sony SRG-300SE or T.16000M. Keep live mode off until the manual camera controls have been tested at church.

## Run it

See [docs/BUILDING.md](docs/BUILDING.md) for the complete Windows and Mac instructions. The short version:

```bash
python -m venv .venv
```

Activate the environment, install dependencies, then start the app:

```bash
python -m pip install -r requirements.txt
python app.py
```

## Church setup

Follow [docs/CHURCH_SETUP.md](docs/CHURCH_SETUP.md) when testing with the Mac, camera, and joystick.

## Project layout

```text
app.py                 Application launcher
ptz_controller/        Camera protocol, joystick input, and desktop UI
tests/                 VISCA packet tests
requirements.txt       Optional joystick dependency
ui-prototype/          Earlier browser UI concept
docs/                  Setup, build, release, and implementation guides
```

## Future work

The next milestone is a real Mac hardware test: manual VISCA commands first, then joystick axis calibration and button mapping. The longer-term UI may still move to Tauri/Rust, but Python is the active path to a usable first controller.

GitHub: <https://github.com/oscarkflin/PTZ_Controller>
