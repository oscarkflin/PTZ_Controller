# PTZ Local

Independent Python + local web controller for a Sony SRG-300SE. This is not a port of oscarkflin/PTZ_Controller: that source was unavailable for inspection.

## Start

Double-click **PTZ Local.app** on the Desktop for automatic startup and browser opening. Reopening it reuses an existing controller. The server keeps running when the browser closes. Logs are in `~/Library/Logs/PTZ Local/server.log`. This launcher uses the Python installation already on this Mac; keep `~/PTZ-Local` in place.

Double-click **Start PTZ Local.command**, or run:

```sh
cd ~/PTZ-Local
python3 server.py --host 0.0.0.0
```

Open http://localhost:8765 on the Mac. On an iPad on the same network, open `http://<Mac Wi-Fi IP>:8765`. Find that IP in System Preferences → Network, or the launcher output. Allow incoming Python connections if macOS asks. Keep the Mac awake and the Terminal window open. Control-C stops the service.

The launcher allows access from the local network, without login or encryption. Use a trusted LAN; do not forward its port to the Internet. For Mac-only use, `python3 server.py` binds to loopback. There are no pip dependencies, cloud services, or Xcode requirements.

## Camera setup

Starts in demo mode; commands are simulated until you select **Sony VISCA over IP**, enter the camera's private IPv4 address, and apply. The default UDP port is 52381 with Sony's eight-byte packet header. Settings persist in `camera.json`.

Sony's SRG-300SE requires firmware 2.0+ and its VISCA interface set to IP:
https://www.sony.jp/remote-camera/support/download/srg-300se/version_up.html

Pan/tilt joystick, variable-speed zoom, home, and six preset slots are implemented. Drag the joystick farther from center for higher speed, up to the speed slider setting; release to stop. Keyboard arrows also control movement. UI presets 1–6 correspond to VISCA memory indices 0–5. Use Rename under a preset to set its label (40 characters maximum; blank restores the default). Labels persist in preset-names.json on the Mac and load on both Mac and iPad; renaming does not change camera memory. Saving a position requires confirmation and overwrites the selected camera preset. Hold Wide or Tele to zoom continuously; release to stop. Holding +/− on the keyboard does the same. Pointer cancellation, lost capture, and window blur also stop held motion. Release-stop bypasses queued requests; browser command numbers let the server reject older motion that arrives afterward. Stop prioritizes the active axis and attempts both pan/tilt and zoom. Stop retries alternate axes over 800 ms unless a new command starts. No stop waits for camera acknowledgements. The server watchdog stops motion if heartbeat updates cease. Keyboard arrows and +/− work when focus is outside form controls. Space stops motion. A server watchdog sends stop after 750 ms without a held-motion refresh.

**Live control** starts OFF on every server launch. While OFF, the server blocks camera commands from every browser; preset renaming remains available. Enter connection settings and turn the switch ON to save them and allow commands immediately. Enabling sends Sony’s sequence-reset packet before starting commands at sequence 1, to handle app restarts. It does not require a connection inquiry or acknowledgement. Turning OFF sends final stop commands, then blocks further camera commands. The switch is shared between Mac and iPad, and other pages refresh its state every two seconds. This is a command gate, not continuous camera connectivity monitoring. Settings can only be edited while OFF.

Joystick, held zoom, stop, and preset commands do not wait for camera replies. Sent means the packet was handed to the network; it does not confirm execution. Real-camera testing is still required. Stop delivery is best effort during network loss. No live video, ONVIF, discovery, or autofocus is included.


## Checks

```sh
python3 -m unittest discover -s tests -v
```
