# Building PTZ Controller

## Current status

The repository currently contains a browser-based UI prototype. It can be previewed on Windows or macOS, but it is not yet a Tauri application and cannot produce a working `.dmg` or `.exe`.

This guide records the exact workflow to use once the real Tauri application has been added to the repository.

## 1. Preview the current UI prototype

The prototype needs only a modern web browser.

1. Clone the repository.
2. Open `ui-prototype/index.html` in a browser.

Or, in the `ui-prototype` directory, run a local static server:

```powershell
python -m http.server 4173
```

Then browse to <http://127.0.0.1:4173>.

The prototype uses simulated joystick values and never sends camera commands.

## 2. Windows development setup

Use Windows to develop and review the interface, mock camera behavior, Rust mapping logic, and the Windows installer.

Install:

1. **Node.js LTS**
2. **Rust stable MSVC toolchain**
3. **Microsoft C++ Build Tools** with **Desktop development with C++** selected
4. Microsoft Edge WebView2 (normally already present on current Windows)

After the Tauri application is scaffolded, from the repository root run:

```powershell
npm install
npm run tauri dev
```

This starts a desktop development window with live reload.

To create a Windows installer:

```powershell
npm run tauri build
```

The generated installer will be in the Tauri `target/release/bundle` directory.

## 3. macOS development and `.dmg` build

Use a Mac to test the real T.16000M joystick and Sony camera. A Mac is also required for local macOS code signing and notarization.

Install on the Mac:

1. Xcode Command Line Tools:

   ```bash
   xcode-select --install
   ```

2. Node.js LTS
3. Rust stable toolchain
4. Clone the repository:

   ```bash
   git clone https://github.com/oscarkflin/PTZ_Controller.git
   cd PTZ_Controller
   ```

After the Tauri application is scaffolded:

```bash
npm install
npm run tauri dev
```

Connect the USB joystick and Sony camera only after the app opens. Verify on-screen VISCA controls before enabling joystick mappings.

To make a Mac disk image:

```bash
npm run tauri build -- --bundles dmg
```

The `.dmg` will be generated in the Tauri `target/release/bundle/dmg` directory. It can be opened and installed by dragging the app to Applications.

## 4. Signing and notarization for a shareable Mac build

An unsigned test build may trigger a macOS security warning. Before giving the application to other operators, use an Apple Developer account to:

1. Create a **Developer ID Application** signing certificate.
2. Configure the certificate in the Mac Keychain or securely in GitHub Actions secrets.
3. Provide Apple notarization credentials.
4. Build and notarize the `.dmg`.

Never commit certificates, private keys, Apple passwords, or API keys to Git.

## 5. Build releases on GitHub

GitHub Actions can build the Windows installer and Mac `.dmg` without manually building on both machines. The workflow will be added after the Tauri app is scaffolded and has a successful local build.

The intended release process:

```text
Finish and test a version
        ↓
Create and push a version tag, for example v0.1.0
        ↓
GitHub Actions builds Windows + macOS installers
        ↓
Review the generated GitHub Release draft
        ↓
Publish the release
```

Example tag commands:

```bash
git tag v0.1.0
git push origin v0.1.0
```

After publication, operators download the appropriate asset from the repository's **Releases** page.

## Build safety checklist

Before calling any installer a release candidate:

- Test Pan, Tilt, Zoom, and Stop against the physical SRG-300SE.
- Test joystick center/dead-zone behavior and joystick disconnection.
- Test every configured preset recall.
- Verify the macOS installer on a Mac other than the build machine when possible.
- Confirm no camera passwords, private keys, or local network details were committed.
