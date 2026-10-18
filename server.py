#!/usr/bin/env python3
"""Local PTZ controller. Python standard library only."""
import argparse
import ipaddress
import json
import secrets
import socket
import struct
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CONFIG = ROOT / 'camera.json'
PRESETS = ROOT / 'preset-names.json'


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('Expected an integer between %s and %s' % (low, high))
    return value


def command(data):
    action = data.get('action')
    if action == 'move':
        x = integer(data.get('x'), -1, 1)
        y = integer(data.get('y'), -1, 1)
        speed = integer(data.get('speed'), 1, 7)
        return bytes([0x81, 1, 6, 1, speed, speed,
                      { -1: 1, 0: 3, 1: 2}[x], {-1: 1, 0: 3, 1: 2}[y], 0xff])
    if action == 'zoom':
        direction = integer(data.get('direction'), -1, 1)
        speed = integer(data.get('speed'), 1, 7)
        return bytes([0x81, 1, 4, 7, 0 if not direction else (0x20 if direction > 0 else 0x30) + speed, 0xff])
    if action == 'home':
        return bytes.fromhex('81 01 06 04 ff')
    if action in ('recall', 'save'):
        preset = integer(data.get('preset'), 0, 15)
        return bytes([0x81, 1, 4, 0x3f, 1 if action == 'save' else 2, preset, 0xff])
    raise ValueError('Unknown action')


def validate_config(data):
    mode = data.get('mode', 'demo')
    if mode not in ('demo', 'visca-udp'):
        raise ValueError('Unsupported camera mode')
    host = str(data.get('host', '')).strip()
    if mode != 'demo':
        address = ipaddress.ip_address(host)
        if address.version != 4 or not address.is_private or address.is_multicast or address.is_unspecified:
            raise ValueError('Use a private IPv4 camera address')
    framing = data.get('framing', 'sony')
    if framing not in ('sony', 'raw'):
        raise ValueError('Invalid packet format')
    return dict(mode=mode, host=host, port=integer(data.get('port', 52381), 1, 65535), framing=framing)


class Controller:
    def __init__(self):
        self.lock = threading.RLock()
        self.config = validate_config(json.loads(CONFIG.read_text())) if CONFIG.exists() else validate_config({})
        self.sequence = 0
        self.connection_status = 'unverified'
        self.live = False
        self.preset_names = json.loads(PRESETS.read_text()) if PRESETS.exists() else {}
        self.moving = False
        self.stop_retry_until = 0
        self.motion_action = 'move'
        self.stop_retry_index = 0
        self.client_orders = {}
        self.last_motion = 0
        self.last_event = 'Live control OFF — camera commands blocked'

    def set_live(self, enabled):
        if type(enabled) is not bool:
            raise ValueError('Live control must be on or off')
        with self.lock:
            if not enabled:
                try:
                    if self.live:
                        self.stop()
                finally:
                    self.live = False
                    self.moving = False
                    self.last_event = 'Live control OFF — camera commands blocked'
            elif not self.live:
                if self.config['mode'] == 'demo':
                    raise ValueError('Select Sony VISCA over IP before enabling live control')
                # Camera counter survives app restarts. Reset it before starting
                # this controller's sequence, without requiring a camera reply.
                self.reset_sequence()
                self.live = True
                self.last_event = 'Live control ON — camera commands enabled'

    def receive(self, sock, sequence):
        deadline = time.monotonic() + .8
        while time.monotonic() < deadline:
            sock.settimeout(max(.01, deadline-time.monotonic()))
            reply, address = sock.recvfrom(1024)
            if address != (self.config['host'], self.config['port']):
                continue
            if self.config['framing'] == 'sony':
                if len(reply) < 8:
                    continue
                kind, length, seq = struct.unpack('!HHI', reply[:8])
                if seq != sequence or length != len(reply)-8:
                    continue
                if kind == 0x0201:
                    raise OSError('Camera reports a VISCA sequence error. Turn Live control off and on to reset the session.')
                if kind != 0x0111:
                    continue
                reply = reply[8:]
            if len(reply) >= 3 and reply[0] == 0x90 and reply[-1] == 0xff:
                if reply[1] & 0xf0 == 0x60:
                    errors = {2:'syntax error',3:'command buffer full',4:'command cancelled',5:'no socket',0x41:'command not executable (check camera mode and preset)'}
                    raise OSError('Camera rejected command: '+errors.get(reply[2], 'error 0x%02x' % reply[2]))
                return reply
        raise TimeoutError('No acknowledgement from camera')

    def send(self, payload, confirm=False):
        if self.config['mode'] != 'demo':
            self.sequence = (self.sequence + 1) & 0xffffffff
            packet = payload
            if self.config['framing'] == 'sony':
                packet = struct.pack('!HHI', 0x0100, len(payload), self.sequence) + payload
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(packet, (self.config['host'], self.config['port']))
                if confirm:
                    reply = self.receive(sock, self.sequence)
                    if reply[1] & 0xf0 not in (0x40, 0x50):
                        raise OSError('Unexpected camera acknowledgement')

    def inquire(self, payload):
        self.sequence = (self.sequence + 1) & 0xffffffff
        packet = payload if self.config['framing'] == 'raw' else struct.pack('!HHI', 0x0110, len(payload), self.sequence)+payload
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.sendto(packet, (self.config['host'], self.config['port']))
            return self.receive(sock, self.sequence)

    def reset_sequence(self, confirm=False):
        if self.config['framing'] != 'sony':
            return
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(.8)
            sock.sendto(bytes.fromhex('02 00 00 01 00 00 00 00 01'), (self.config['host'], self.config['port']))
            if confirm:
                reply, address = sock.recvfrom(1024)
                if address != (self.config['host'], self.config['port']) or reply[:4] != bytes.fromhex('02 01 00 01') or reply[8:] != b'\x01':
                    raise OSError('No valid VISCA sequence reset acknowledgement')
        self.sequence = 0

    def zoom_step(self, direction):
        integer(direction, -1, 1)
        if not direction:
            raise ValueError('Choose wide or tele')
        if self.config['mode'] == 'demo':
            self.last_event = 'Demo: zoom step'
            return
        reply = self.inquire(bytes.fromhex('81 09 04 47 ff'))
        if len(reply) != 7 or reply[:2] != b'\x90\x50' or any(n > 15 for n in reply[2:6]):
            raise OSError('Invalid zoom position reply')
        position = 0
        for nibble in reply[2:6]:
            position = (position << 4) | nibble
        target = min(0x4000, max(0, position + direction * 0x200))
        nibbles = [(target >> shift) & 15 for shift in (12,8,4,0)]
        self.send(bytes([0x81,1,4,0x47]+nibbles+[0xff]), confirm=True)
        self.last_event = 'Camera accepted zoom step (fixed target, automatic stop)'

    def rename_preset(self, data):
        preset = integer(data.get('preset'), 0, 5)
        name = data.get('name')
        if not isinstance(name, str) or len(name.strip()) > 40:
            raise ValueError('Use a preset name of up to 40 characters')
        with self.lock:
            names = dict(self.preset_names)
            names[str(preset)] = name.strip()
            temp = PRESETS.with_suffix('.tmp')
            temp.write_text(json.dumps(names, indent=2))
            temp.replace(PRESETS)
            self.preset_names = names
            self.last_event = 'Preset name saved'

    def check_connection(self):
        """Request pan/tilt position; this inquiry does not move the camera."""
        with self.lock:
            if self.config['mode'] == 'demo':
                self.connection_status = 'demo'
                self.last_event = 'Demo mode — no camera commands are sent'
                return
            self.connection_status = 'unreachable'
            try:
                self.reset_sequence(confirm=True)
                reply = self.inquire(bytes.fromhex('81 09 06 12 ff'))
                if len(reply) != 11 or reply[:2] != b'\x90\x50':
                    raise OSError('Unexpected pan/tilt position reply')
                self.connection_status = 'responding'
                self.last_event = 'Camera responding — VISCA session reset and position confirmed'
            except OSError as error:
                self.last_event = 'Connection check failed: ' + str(error)

    def stop(self):
        self.moving = False
        self.stop_retry_until = time.monotonic() + .8
        self.stop_retry_index = 0
        error = None
        # Prioritize the axis that was moving, but attempt both even if one fails.
        for payload in self.stop_packets():
            try:
                self.send(payload)
            except OSError as exc:
                error = exc
        if error:
            raise error
        self.last_event = 'Stop sent' if self.config['mode'] != 'demo' else 'Demo stopped'

    def stop_packets(self):
        pan = command(dict(action='move', x=0, y=0, speed=1))
        zoom = command(dict(action='zoom', direction=0, speed=1))
        return (zoom, pan) if self.motion_action == 'zoom' else (pan, zoom)

    def execute(self, data):
        with self.lock:
            if not self.live:
                self.last_event = 'Live control OFF — camera commands blocked'
                return
            if 'client' in data:
                client = data['client']
                if not isinstance(client, str) or not 1 <= len(client) <= 80:
                    raise ValueError('Invalid controller session')
                order = integer(data.get('order'), 1, 2**53-1)
                if order <= self.client_orders.get(client, 0):
                    return  # A release-stop already superseded this delayed request.
                if len(self.client_orders) >= 256 and client not in self.client_orders:
                    raise ValueError('Too many browser sessions; restart the service')
                self.client_orders[client] = order
            if data.get('action') == 'stop':
                self.stop()
            elif data.get('action') == 'zoom-step':
                self.zoom_step(data.get('direction'))
            else:
                payload = command(data)
                # Discrete commands must not interrupt the browser heartbeat for held motion.
                confirmed = False
                self.send(payload)
                self.stop_retry_until = 0
                if data['action'] in ('move', 'zoom'):
                    self.motion_action = data['action']
                    self.moving = True
                    self.last_motion = time.monotonic()
                self.last_event = ('Demo: ' if self.config['mode'] == 'demo' else 'Camera accepted: ' if confirmed else 'Sent: ') + data['action']

    def check_timeout(self):
        with self.lock:
            if self.moving and time.monotonic() - self.last_motion > .75:
                try:
                    self.stop()
                except OSError:
                    self.last_event = 'Stop could not be sent; check network'
            elif self.live and time.monotonic() < self.stop_retry_until:
                try:
                    # Space retries instead of repeatedly bursting both commands.
                    self.send(self.stop_packets()[self.stop_retry_index % 2])
                    self.stop_retry_index += 1
                except OSError:
                    self.last_event = 'Stop retry failed; check network'

    def watchdog(self):
        while True:
            time.sleep(.1)
            self.check_timeout()


def make_handler(controller, token):
    class Handler(BaseHTTPRequestHandler):
        def respond(self, status, value):
            body = json.dumps(value).encode()
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == '/api/state':
                with controller.lock:
                    self.respond(200, dict(config=controller.config, event=controller.last_event, token=token, preset_names=controller.preset_names, connection_status=controller.connection_status, live=controller.live))
                return
            paths = {'/': ('index.html', 'text/html'), '/app.js': ('app.js', 'text/javascript'), '/style.css': ('style.css', 'text/css')}
            if self.path not in paths:
                self.respond(404, {'error': 'Not found'})
                return
            name, content_type = paths[self.path]
            body = (ROOT / 'static' / name).read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', content_type + '; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if not secrets.compare_digest(self.headers.get('X-PTZ-Token', ''), token):
                self.respond(403, {'error': 'Reload the controller page'})
                return
            try:
                size = int(self.headers.get('Content-Length', 0))
                if not 0 < size <= 4096:
                    raise ValueError('Invalid request size')
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError('Expected an object')
                if self.path == '/api/config':
                    config = validate_config(data)
                    with controller.lock:
                        if controller.live:
                            raise ValueError('Turn live control off before editing connection settings')
                        temp = CONFIG.with_suffix('.tmp')
                        temp.write_text(json.dumps(config, indent=2))
                        temp.replace(CONFIG)
                        controller.config = config
                        controller.last_event = 'Settings saved — live control is OFF'
                elif self.path == '/api/live':
                    controller.set_live(data.get('enabled'))
                elif self.path == '/api/preset-name':
                    controller.rename_preset(data)
                elif self.path == '/api/command':
                    controller.execute(data)
                else:
                    self.respond(404, {'error': 'Not found'})
                    return
                self.respond(200, {'event': controller.last_event, 'connection_status': controller.connection_status, 'live': controller.live})
            except (ValueError, TypeError, KeyError) as exc:
                self.respond(400, {'error': str(exc)})
            except OSError as exc:
                self.respond(502, {'error': str(exc)})
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1', help='Use 0.0.0.0 for iPad access on trusted LAN')
    parser.add_argument('--port', type=int, default=8765)
    args = parser.parse_args()
    controller = Controller()
    server = ThreadingHTTPServer((args.host, args.port), make_handler(controller, secrets.token_hex(24)))
    threading.Thread(target=controller.watchdog, daemon=True).start()
    print('PTZ Local: http://localhost:%s' % args.port, flush=True)
    if args.host == '0.0.0.0':
        print('iPad: http://<Mac Wi-Fi IP>:%s (same network). Trusted LAN only; no user authentication.' % args.port, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        with controller.lock:
            if controller.live:
                controller.set_live(False)
        server.server_close()


if __name__ == '__main__':
    main()
