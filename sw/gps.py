"""GPS UART + parser NMEA básico.

Compatible con frases GLL, RMC y GSV, siguiendo el proyecto ESP32 original.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import threading
import time
from typing import Optional

try:
    import serial
except Exception:  # pragma: no cover - permite arrancar sin dependencia instalada
    serial = None


@dataclass
class GPSData:
    utcHour: int = 0
    utcMinute: int = 0
    utcSecond: int = 0
    utcDay: int = 0
    utcMonth: int = 0
    utcYear: int = 0
    utcValid: bool = False
    lat: Optional[float] = None
    lon: Optional[float] = None
    speed: float = 0.0  # km/h
    course: float = 0.0
    sats: int = 0
    fix: bool = False
    last_sentence: str = ""
    last_update: float = 0.0

    @property
    def utc(self) -> Optional[str]:
        if not self.utcValid:
            return None
        try:
            return datetime(
                self.utcYear,
                self.utcMonth,
                self.utcDay,
                self.utcHour,
                self.utcMinute,
                self.utcSecond,
                tzinfo=timezone.utc,
            ).isoformat().replace("+00:00", "Z")
        except Exception:
            return None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["utc"] = self.utc
        d["dir"] = course_to_text(self.course) if self.fix else "---"
        return d


def course_to_text(deg: float) -> str:
    dirs = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
    try:
        return dirs[int((float(deg) + 22.5) / 45.0) % 8]
    except Exception:
        return "---"


def _to_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _to_int(value: str, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _conv_lat(value: str, hemi: str) -> Optional[float]:
    if len(value) < 4:
        return None
    deg = _to_float(value[:2])
    minutes = _to_float(value[2:])
    out = deg + minutes / 60.0
    return -out if hemi == "S" else out


def _conv_lon(value: str, hemi: str) -> Optional[float]:
    if len(value) < 5:
        return None
    deg = _to_float(value[:3])
    minutes = _to_float(value[3:])
    out = deg + minutes / 60.0
    return -out if hemi == "W" else out


def _strip_checksum(line: str) -> str:
    return line.split("*", 1)[0].strip()


class GPSReader:
    def __init__(self, port: str = "/dev/serial0", baudrate: int = 9600, enabled: bool = True):
        self.port = port
        self.baudrate = baudrate
        self.enabled = enabled
        self._data = GPSData()
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self.error: Optional[str] = None

    def start(self) -> None:
        if not self.enabled:
            self.error = "GPS desactivado en config.py"
            return
        self._thread = threading.Thread(target=self._loop, daemon=True, name="gps-reader")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def snapshot(self) -> GPSData:
        with self._lock:
            return GPSData(**asdict(self._data))

    def _loop(self) -> None:
        if serial is None:
            self.error = "Falta pyserial. Instala requirements.txt"
            return
        while not self._stop.is_set():
            try:
                with serial.Serial(self.port, self.baudrate, timeout=1) as ser:
                    self.error = None
                    while not self._stop.is_set():
                        raw = ser.readline().decode("ascii", errors="ignore").strip()
                        if raw:
                            self.parse(raw)
            except Exception as exc:
                self.error = f"GPS no disponible: {exc}"
                time.sleep(2)

    def parse(self, line: str) -> None:
        clean = _strip_checksum(line)
        parts = clean.split(",")
        if not parts:
            return

        head = parts[0]
        changed = False
        with self._lock:
            self._data.last_sentence = line
            self._data.last_update = time.time()

            if head in ("$GNGLL", "$GPGLL") and len(parts) >= 7:
                lat = _conv_lat(parts[1], parts[2])
                lon = _conv_lon(parts[3], parts[4])
                if lat is not None:
                    self._data.lat = lat
                if lon is not None:
                    self._data.lon = lon
                self._data.fix = parts[6] == "A"
                changed = True

            elif head in ("$GNRMC", "$GPRMC") and len(parts) >= 10:
                utc_time = parts[1]
                status = parts[2]
                self._data.fix = status == "A"
                lat = _conv_lat(parts[3], parts[4]) if len(parts) > 5 else None
                lon = _conv_lon(parts[5], parts[6]) if len(parts) > 6 else None
                if lat is not None:
                    self._data.lat = lat
                if lon is not None:
                    self._data.lon = lon
                self._data.speed = _to_float(parts[7]) * 1.852
                self._data.course = _to_float(parts[8])

                if len(utc_time) >= 6:
                    self._data.utcHour = _to_int(utc_time[0:2])
                    self._data.utcMinute = _to_int(utc_time[2:4])
                    self._data.utcSecond = _to_int(utc_time[4:6])
                    self._data.utcValid = True

                utc_date = parts[9]
                if len(utc_date) >= 6:
                    self._data.utcDay = _to_int(utc_date[0:2])
                    self._data.utcMonth = _to_int(utc_date[2:4])
                    self._data.utcYear = 2000 + _to_int(utc_date[4:6])
                changed = True

            elif head in ("$GPGSV", "$GNGSV") and len(parts) >= 4:
                self._data.sats = _to_int(parts[3])
                changed = True

            if not changed:
                return
