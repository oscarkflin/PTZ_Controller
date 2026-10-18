#!/usr/bin/env python3
"""Start one local service and open its browser UI from Finder."""
import fcntl
import json
import os
import signal
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parent
STATE = Path.home() / 'Library' / 'Logs' / 'PTZ Local'
URL = 'http://127.0.0.1:8765'
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def running():
    try:
        with OPENER.open(URL + '/api/state', timeout=.5) as response:
            data = json.load(response)
            return isinstance(data, dict) and 'config' in data and 'token' in data and 'event' in data
    except (OSError, ValueError, urllib.error.URLError):
        return False


def main():
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / 'launch.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        pidfile = STATE / 'server.pid'
        if pidfile.exists() and (ROOT / 'server.py').stat().st_mtime > pidfile.stat().st_mtime:
            pid = int(pidfile.read_text())
            info = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'command='], capture_output=True, text=True)
            if info.returncode == 0 and str(ROOT / 'server.py') in info.stdout:
                os.kill(pid, signal.SIGINT)
                deadline = time.monotonic() + 10
                while running() and time.monotonic() < deadline:
                    time.sleep(.2)
                if running():
                    raise RuntimeError('The previous controller is still stopping. Wait a moment and open PTZ Local again.')
        if not running():
            with (STATE / 'server.log').open('a') as log:
                process = subprocess.Popen(
                    [sys.executable, str(ROOT / 'server.py'), '--host', '0.0.0.0'],
                    cwd=str(ROOT), stdin=subprocess.DEVNULL, stdout=log,
                    stderr=subprocess.STDOUT, start_new_session=True)
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                if running():
                    (STATE / 'server.pid').write_text(str(process.pid))
                    break
                if process.poll() is not None:
                    raise RuntimeError('The controller could not start. See ~/Library/Logs/PTZ Local/server.log. Port 8765 may already be in use.')
                time.sleep(.2)
            else:
                process.terminate()
                raise RuntimeError('The controller did not become ready. See ~/Library/Logs/PTZ Local/server.log.')
    subprocess.run(['/usr/bin/open', URL], check=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        message = str(error)
        print(message, file=sys.stderr)
        # Pass text as an argument so error messages are never interpreted as code.
        subprocess.run(['/usr/bin/osascript', '-e',
                        'on run argv\ndisplay alert "PTZ Local" message (item 1 of argv) as critical\nend run', message])
        sys.exit(1)
