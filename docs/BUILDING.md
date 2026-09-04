# Build and Run Guide

## What this builds today

The first PTZ Controller is a Python desktop app. You can run it directly on Windows or macOS; no Rust, Node.js, or Tauri setup is needed.

It starts in **demo mode**. Commands are only sent after you enable **Send live camera commands** inside the application.

## Windows: run from source

1. Install Python 3.11 or later from <https://www.python.org/downloads/>.
2. Clone the repository and open PowerShell in the project folder.
3. Create and activate a local virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install joystick support and run the app:

   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   python app.py
   ```

5. Run the protocol tests at any time:

   ```powershell
   python -m unittest discover -s tests -v
   ```

## macOS: run from source

1. Install Python 3.11 or later. Python from <https://www.python.org/downloads/> is recommended for the first test.
2. Open Terminal and clone the project:

   ```bash
   git clone https://github.com/oscarkflin/PTZ_Controller.git
   cd PTZ_Controller
   ```

3. Create and activate a local virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install joystick support and run the app:

   ```bash
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   python app.py
   ```

The PTZ Controller window should open. Connect the camera and USB joystick only after it is visible.

## First camera test

1. Connect the Mac and Sony camera to the same Ethernet network.
2. Enter the Sony camera's IP address and configured UDP VISCA port (`52381` is the default).
3. Leave **Send live camera commands** off and press **Connect**.
4. Turn on live mode only after confirming the IP is correct.
5. Set a low speed, test one movement, then press **STOP**.
6. Verify manual Pan/Tilt/Zoom works before scanning or enabling the joystick.

See [CHURCH_SETUP.md](CHURCH_SETUP.md) for the full field checklist.

## Package an executable later

For a simple test executable, install PyInstaller inside the same virtual environment:

```bash
python -m pip install pyinstaller
pyinstaller --noconfirm --windowed --name PTZController app.py
```

Build on the target operating system:

- Build the Windows `.exe` on Windows.
- Build the macOS `.app` on macOS.

PyInstaller places output in `dist/PTZController/`. A macOS `.dmg` can be created from the generated `.app` later, after real hardware testing and code signing are complete.

Do not distribute unsigned Mac builds broadly; macOS may block or warn about them. See [RELEASING.md](RELEASING.md) for the signing/release plan.
