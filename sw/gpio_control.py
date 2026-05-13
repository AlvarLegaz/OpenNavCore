"""Control sencillo de salidas GPIO."""
from __future__ import annotations

try:
    from gpiozero import LED
except Exception:  # pragma: no cover
    LED = None


class GPIOControl:
    def __init__(self, lights_pin: int = 17, enabled: bool = True):
        self.lights_pin = lights_pin
        self.enabled = enabled
        self._lights = None
        self.error = None
        self.lights_state = False

    def start(self) -> None:
        if not self.enabled:
            self.error = "GPIO desactivado en config.py"
            return
        if LED is None:
            self.error = "Falta gpiozero. Instala requirements.txt"
            return
        try:
            self._lights = LED(self.lights_pin)
            self.off()
        except Exception as exc:
            self.error = f"GPIO no disponible: {exc}"

    def on(self) -> str:
        self.lights_state = True
        if self._lights:
            self._lights.on()
        return "Luces ON"

    def off(self) -> str:
        self.lights_state = False
        if self._lights:
            self._lights.off()
        return "Luces OFF"

    def status(self) -> dict:
        return {"enabled": self.enabled, "pin": self.lights_pin, "lights": self.lights_state, "error": self.error}
