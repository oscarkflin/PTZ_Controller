#!/bin/zsh
cd -- "${0:A:h}"
PYTHON_BIN="$(command -v python3)"
if [[ -z "$PYTHON_BIN" ]]; then
  echo "Python 3 is required. Install Python from python.org."
  read -r "?Press Return to close."
  exit 1
fi
echo "Open http://localhost:8765 on this Mac."
echo "For iPad access, use http://<this Mac's Wi-Fi IP>:8765 on the same network."
echo "Mac Wi-Fi IP (if available):"
ipconfig getifaddr en0
"$PYTHON_BIN" server.py --host 0.0.0.0
read -r "?Press Return to close."
