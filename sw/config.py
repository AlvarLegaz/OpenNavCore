"""Configuración central del rover para Raspberry Pi.

Edita este archivo si tus pines, puertos o resoluciones son distintos.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class CameraConfig:
    high_size: tuple[int, int] = (1280, 720)
    low_size: tuple[int, int] = (640, 360)
    high_fps: int = 10
    low_fps: int = 12
    jpeg_quality_high: int = 80
    jpeg_quality_low: int = 65
    rotate_180: bool = True


@dataclass(frozen=True)
class GPSConfig:
    enabled: bool = True
    # En Raspberry Pi el UART principal suele ser /dev/serial0.
    port: str = "/dev/serial0"
    baudrate: int = 9600


@dataclass(frozen=True)
class I2CConfig:
    enabled: bool = True
    bus: int = 1
    mpu9250_addr: int = 0x68
    bmp280_addr_candidates: tuple[int, int] = (0x76, 0x77)
    sea_level_hpa: float = 1013.25


@dataclass(frozen=True)
class GPIOConfig:
    enabled: bool = True
    # GPIO BCM, no número físico del pin. GPIO17 = pin físico 11.
    lights_pin: int = 17


@dataclass(frozen=True)
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 8000


@dataclass(frozen=True)
class UDPConfig:
    enabled: bool = True
    video_payload_size: int = 1000
    telemetry_interval_s: float = 0.2
    client_timeout_s: float = 15.0


CAMERA = CameraConfig()
GPS = GPSConfig()
I2C = I2CConfig()
GPIO = GPIOConfig()
SERVER = ServerConfig()
UDP = UDPConfig()
