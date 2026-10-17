# Android phone test app

The Android app connects straight to the Sony SRG-300SE over Wi-Fi using UDP VISCA. No Mac, Python server, website hosting, or computer is required while operating it.

## First version

- Android 8.0 or newer
- Editable camera IPv4 address and UDP port (default 52381)
- Demo mode at startup; explicitly enable live commands
- Hold Pan/Tilt/Zoom buttons to move, release to send Stop
- Stop All sends both pan/tilt and zoom stop
- Leaving the app disables live mode and attempts to stop the camera
- Preset recall; long-press a preset to rename, store position, or remove its local button
- Add new preset buttons with an unused camera slot 0–15
- Camera address and preset names persist on the phone

There is no USB joystick input, video preview, camera discovery, or camera acknowledgement tracking in this initial build. A message saying a command was sent does not prove that the camera received it. Stops also depend on a functioning network. Camera command compatibility still needs testing with the physical SRG-300SE.

## Download and install on your phone

1. Open the repository's **Actions** tab: https://github.com/oscarkflin/PTZ_Controller/actions
2. Select **Android test APK**, then a successful run. If needed, use **Run workflow** to build again.
3. Under **Artifacts**, download **PTZ-Controller-Android-test**. You may need to sign in to GitHub.
4. Extract the downloaded ZIP. Open `app-debug.apk` on the Android phone. You can download directly on the phone or copy the APK over USB.
5. If Android asks, permit installation from the particular browser or file manager you are using. This is a test APK; no Play Store installation is required.

Debug builds on separate computers/runners can have different signing keys. If Android refuses an update because the signatures differ, uninstall the older test version first. This removes its saved local settings and preset labels but does not erase camera presets.

## Test at church

1. Put the phone on church Wi-Fi that can reach the camera's wired network. Guest Wi-Fi often blocks local devices; use an approved network with camera access.
2. Open **PTZ Controller**. Enter the camera's actual IPv4 address and VISCA UDP port.
3. Try the controls in demo mode first.
4. Enable **live camera commands**, then start at a low speed.
5. Hold a direction briefly and release. Confirm the camera stops; test **STOP ALL** and zoom next.
6. Recall a known preset. Long-press its button to rename the label or store a new camera position with confirmation.

Adding or renaming a button changes the phone's labels only. To create/change the shot stored in the camera, frame the camera and use **Store current camera position**. Removing a local button leaves the camera's stored position intact.

## Build yourself

Open the `android` folder in Android Studio. Use JDK 17, Android SDK 35, Gradle 8.9, and Android Gradle Plugin 8.7.3. Select **Build APK(s)**, or run from the repository root with Gradle 8.9 installed:

```bash
gradle -p android assembleDebug
```

Output: `android/app/build/outputs/apk/debug/app-debug.apk`.

The GitHub workflow installs these tools and builds the same target automatically when Android files change on `main`.
