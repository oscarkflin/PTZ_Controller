"""Sony VISCA-over-IP UDP commands for the SRG-300SE MVP."""

from __future__ import annotations

import socket
import struct


class ViscaClient:
    """Sends the small set of VISCA commands needed by the first MVP.

    Sony VISCA-over-IP wraps each conventional VISCA payload in an eight-byte
    header: payload type, payload length, then an increasing sequence number.
    Commands must be verified against the physical SRG-300SE before live use.
    """

    def __init__(self, host: str, port: int = 52381, *, enabled: bool = False) -> None:
        self.host = host
        self.port = int(port)
        self.enabled = enabled
        self._sequence = 0
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def close(self) -> None:
        self._socket.close()

    def _packet(self, payload: bytes) -> bytes:
        packet = struct.pack(">HHI", 0x0100, len(payload), self._sequence) + payload
        self._sequence = (self._sequence + 1) & 0xFFFFFFFF
        return packet

    def send(self, payload: bytes) -> bytes:
        packet = self._packet(payload)
        if self.enabled:
            self._socket.sendto(packet, (self.host, self.port))
        return packet

    def pan_tilt(self, pan: int, tilt: int, pan_speed: int, tilt_speed: int) -> bytes:
        """Move in normalized directions (-1, 0, 1); zeroes stop movement."""
        pan_direction = {-1: 0x01, 0: 0x03, 1: 0x02}[max(-1, min(1, pan))]
        tilt_direction = {-1: 0x02, 0: 0x03, 1: 0x01}[max(-1, min(1, tilt))]
        return self.send(
            bytes((0x81, 0x01, 0x06, 0x01, max(1, min(24, pan_speed)), max(1, min(20, tilt_speed)), pan_direction, tilt_direction, 0xFF))
        )

    def stop(self) -> bytes:
        return self.pan_tilt(0, 0, 1, 1)

    def zoom(self, direction: int, speed: int = 4) -> bytes:
        """Move zoom: +1 tele, -1 wide, 0 stop."""
        speed = max(0, min(7, speed))
        command = 0x20 + speed if direction > 0 else 0x30 + speed if direction < 0 else 0x00
        return self.send(bytes((0x81, 0x01, 0x04, 0x07, command, 0xFF)))

    def recall_preset(self, preset: int) -> bytes:
        if not 0 <= preset <= 15:
            raise ValueError("Preset must be between 0 and 15.")
        return self.send(bytes((0x81, 0x01, 0x04, 0x3F, 0x02, preset, 0xFF)))
