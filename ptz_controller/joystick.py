"""Optional pygame joystick input for the first controller release."""

from __future__ import annotations

from dataclasses import dataclass

try:
    import pygame
except ImportError:  # The GUI remains usable for manual VISCA tests.
    pygame = None


@dataclass
class JoystickState:
    x: float = 0.0
    y: float = 0.0
    twist: float = 0.0
    throttle: float = 0.0
    buttons: tuple[bool, ...] = ()


class JoystickReader:
    def __init__(self) -> None:
        self.device = None
        self.name = "No joystick detected"
        if pygame is not None:
            pygame.init()
            pygame.joystick.init()

    @property
    def available(self) -> bool:
        return pygame is not None

    def connect_first(self) -> bool:
        if pygame is None:
            return False
        pygame.event.pump()
        if pygame.joystick.get_count() < 1:
            self.device = None
            self.name = "No joystick detected"
            return False
        self.device = pygame.joystick.Joystick(0)
        self.device.init()
        self.name = self.device.get_name()
        return True

    def read(self) -> JoystickState:
        if self.device is None:
            return JoystickState()
        pygame.event.pump()
        axes = [self.device.get_axis(index) for index in range(self.device.get_numaxes())]
        buttons = tuple(bool(self.device.get_button(index)) for index in range(self.device.get_numbuttons()))
        # These default axis positions must be confirmed in the calibration UI
        # on each OS; unrecognized/missing axes are safely treated as zero.
        get = lambda index: axes[index] if len(axes) > index else 0.0
        return JoystickState(x=get(0), y=-get(1), twist=get(2), throttle=(get(3) + 1) / 2, buttons=buttons)
