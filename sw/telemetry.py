"""Capa unificada de telemetría."""
from __future__ import annotations

import os
import time
from typing import Any

from gps import GPSReader
from imu import IMUReader


def format_uptime(seconds: float) -> str:
    total = int(seconds)
    days = total // 86400
    hours = (total // 3600) % 24
    minutes = (total // 60) % 60
    secs = total % 60
    return f"{days}d {hours:02d}:{minutes:02d}:{secs:02d}"


def cpu_temp() -> float | None:
    path = "/sys/class/thermal/thermal_zone0/temp"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return round(int(f.read().strip()) / 1000.0, 1)
    except Exception:
        return None


class Telemetry:
    def __init__(self, gps: GPSReader, imu: IMUReader):
        self.gps = gps
        self.imu = imu
        self.started_at = time.monotonic()

    def full(self) -> dict[str, Any]:
        gps_data = self.gps.snapshot().to_dict()
        imu_data = self.imu.snapshot().to_dict()
        temp = imu_data.get("temp") or cpu_temp() or 0.0
        return {
            "temp": round(float(temp), 1),
            "bat": 0.0,  # De momento no hay sensor de batería definido en Raspberry.
            "uptime": format_uptime(time.monotonic() - self.started_at),
            "gps": gps_data,
            "imu": {
                "roll": round(imu_data.get("roll", 0.0), 2),
                "pitch": round(imu_data.get("pitch", 0.0), 2),
                "yaw": round(imu_data.get("yaw", 0.0), 2),
                "alt": round(imu_data.get("altitude", 0.0), 2),
                "pres": round(imu_data.get("pressure", 0.0), 2),
            },
        }

    def system(self) -> dict[str, Any]:
        imu_data = self.imu.snapshot().to_dict()
        return {
            "temp": round(float(imu_data.get("temp") or cpu_temp() or 0.0), 1),
            "bat": 0.0,
            "uptime": format_uptime(time.monotonic() - self.started_at),
            "pid": os.getpid(),
        }

    def gps_json(self) -> dict[str, Any]:
        return self.gps.snapshot().to_dict()

    def imu_json(self) -> dict[str, Any]:
        imu = self.imu.snapshot().to_dict()
        return {
            "ok": bool(imu.get("okMPU") or imu.get("okBMP")),
            "okMPU": imu.get("okMPU"),
            "okBMP": imu.get("okBMP"),
            "roll": round(imu.get("roll", 0.0), 2),
            "pitch": round(imu.get("pitch", 0.0), 2),
            "yaw": round(imu.get("yaw", 0.0), 2),
            "alt": round(imu.get("altitude", 0.0), 2),
            "pres": round(imu.get("pressure", 0.0), 2),
            "temp": round(imu.get("temp", 0.0), 2),
            "raw": imu,
        }
