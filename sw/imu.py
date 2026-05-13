"""Lectura básica MPU9250 + BMP280 por I2C.

El MPU9250 se lee directamente por registros. El yaw es relativo por giroscopio,
igual que en el proyecto ESP32 original: no es una brújula absoluta.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import math
import threading
import time
from typing import Optional

try:
    from smbus2 import SMBus
except Exception:  # pragma: no cover
    SMBus = None


@dataclass
class IMUData:
    okMPU: bool = False
    okBMP: bool = False
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0
    ax: float = 0.0
    ay: float = 0.0
    az: float = 0.0
    gx: float = 0.0
    gy: float = 0.0
    gz: float = 0.0
    mx: float = 0.0
    my: float = 0.0
    mz: float = 0.0
    temp: float = 0.0
    pressure: float = 0.0
    altitude: float = 0.0
    error: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class IMUReader:
    PWR_MGMT_1 = 0x6B
    ACCEL_XOUT_H = 0x3B
    GYRO_XOUT_H = 0x43

    def __init__(self, bus_id: int = 1, mpu_addr: int = 0x68, bmp_addrs=(0x76, 0x77), sea_level_hpa: float = 1013.25, enabled: bool = True):
        self.bus_id = bus_id
        self.mpu_addr = mpu_addr
        self.bmp_addrs = bmp_addrs
        self.sea_level_hpa = sea_level_hpa
        self.enabled = enabled
        self._lock = threading.Lock()
        self._data = IMUData()
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._bus = None
        self._bmp = None
        self._gx_off = 0.0
        self._gy_off = 0.0
        self._gz_off = 0.0
        self._roll = 0.0
        self._pitch = 0.0
        self._yaw = 0.0

    def start(self) -> None:
        self._thread = threading.Thread(target=self._loop, daemon=True, name="imu-reader")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def snapshot(self) -> IMUData:
        with self._lock:
            return IMUData(**asdict(self._data))

    def _loop(self) -> None:
        if not self.enabled:
            with self._lock:
                self._data.error = "I2C desactivado en config.py"
            return
        if SMBus is None:
            with self._lock:
                self._data.error = "Falta smbus2. Instala requirements.txt"
            return
        try:
            self._bus = SMBus(self.bus_id)
            self._init_mpu()
            self._init_bmp_best_effort()
            self._calibrate_gyro()
        except Exception as exc:
            with self._lock:
                self._data.error = f"IMU/BMP no disponible: {exc}"
            return

        last = time.monotonic()
        last_bmp = 0.0
        while not self._stop.is_set():
            now = time.monotonic()
            dt = max(0.001, min(now - last, 1.0))
            last = now
            try:
                self._update_mpu(dt)
                if now - last_bmp > 1.0:
                    self._update_bmp()
                    last_bmp = now
            except Exception as exc:
                with self._lock:
                    self._data.error = str(exc)
            time.sleep(0.02)

    def _init_mpu(self) -> None:
        self._bus.write_byte_data(self.mpu_addr, self.PWR_MGMT_1, 0x00)
        time.sleep(0.1)
        with self._lock:
            self._data.okMPU = True

    def _init_bmp_best_effort(self) -> None:
        try:
            import board
            import busio
            import adafruit_bmp280
            i2c = busio.I2C(board.SCL, board.SDA)
            for addr in self.bmp_addrs:
                try:
                    bmp = adafruit_bmp280.Adafruit_BMP280_I2C(i2c, address=addr)
                    bmp.sea_level_pressure = self.sea_level_hpa
                    self._bmp = bmp
                    with self._lock:
                        self._data.okBMP = True
                    return
                except Exception:
                    continue
        except Exception:
            # BMP opcional: el rover puede arrancar sin él.
            return

    def _read_i16(self, reg: int) -> int:
        hi = self._bus.read_byte_data(self.mpu_addr, reg)
        lo = self._bus.read_byte_data(self.mpu_addr, reg + 1)
        value = (hi << 8) | lo
        return value - 65536 if value & 0x8000 else value

    def _read_accel(self):
        ax = self._read_i16(self.ACCEL_XOUT_H) / 16384.0
        ay = self._read_i16(self.ACCEL_XOUT_H + 2) / 16384.0
        az = self._read_i16(self.ACCEL_XOUT_H + 4) / 16384.0
        return ax, ay, az

    def _read_gyro(self):
        gx = self._read_i16(self.GYRO_XOUT_H) / 131.0
        gy = self._read_i16(self.GYRO_XOUT_H + 2) / 131.0
        gz = self._read_i16(self.GYRO_XOUT_H + 4) / 131.0
        return gx, gy, gz

    def _calibrate_gyro(self) -> None:
        sx = sy = sz = 0.0
        n = 120
        for _ in range(n):
            gx, gy, gz = self._read_gyro()
            sx += gx
            sy += gy
            sz += gz
            time.sleep(0.005)
        self._gx_off = sx / n
        self._gy_off = sy / n
        self._gz_off = sz / n

    def _update_mpu(self, dt: float) -> None:
        ax, ay, az = self._read_accel()
        gx, gy, gz = self._read_gyro()
        gx -= self._gx_off
        gy -= self._gy_off
        gz -= self._gz_off

        acc_roll = math.atan2(ay, -az) * 57.2958
        acc_pitch = math.atan2(-ax, math.sqrt(ay * ay + az * az)) * 57.2958

        self._roll = 0.01 * (self._roll + gx * dt) + 0.99 * acc_roll
        self._pitch = 0.01 * (self._pitch + gy * dt) + 0.99 * acc_pitch
        self._yaw = (self._yaw + gz * dt) % 360.0

        with self._lock:
            self._data.ax = ax
            self._data.ay = ay
            self._data.az = az
            self._data.gx = gx
            self._data.gy = gy
            self._data.gz = gz
            self._data.roll = self._roll
            self._data.pitch = -self._pitch
            self._data.yaw = self._yaw
            self._data.okMPU = True
            self._data.error = ""

    def _update_bmp(self) -> None:
        if not self._bmp:
            return
        with self._lock:
            self._data.temp = float(self._bmp.temperature)
            self._data.pressure = float(self._bmp.pressure)
            self._data.altitude = float(self._bmp.altitude)
            self._data.okBMP = True
