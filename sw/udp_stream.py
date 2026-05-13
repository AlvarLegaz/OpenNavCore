"""Streaming UDP simple para vídeo JPEG troceado + telemetría."""
from __future__ import annotations

import json
import socket
import struct
import threading
import time
from typing import Optional, Tuple


MAGIC = 0xCAFE


class UDPStreamer:
    def __init__(self, camera, telemetry, payload_size: int = 1000, telemetry_interval_s: float = 0.2, client_timeout_s: float = 15.0, enabled: bool = True):
        self.camera = camera
        self.telemetry = telemetry
        self.payload_size = payload_size
        self.telemetry_interval_s = telemetry_interval_s
        self.client_timeout_s = client_timeout_s
        self.enabled = enabled
        self.active = False
        self.mode = "low"
        self.client: Optional[Tuple[str, int]] = None
        self.telemetry_client: Optional[Tuple[str, int]] = None
        self.last_ping = 0.0
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.frame_id = 0

    def start(self, ip: str, video_port: int, telemetry_port: int, mode: str = "low") -> dict:
        if not self.enabled:
            return {"ok": False, "error": "UDP desactivado en config.py"}
        with self._lock:
            self.client = (ip, int(video_port))
            self.telemetry_client = (ip, int(telemetry_port))
            self.mode = "high" if mode == "high" else "low"
            self.last_ping = time.monotonic()
            self.active = True
            self._stop.clear()
            if not self._thread or not self._thread.is_alive():
                self._thread = threading.Thread(target=self._loop, daemon=True, name="udp-streamer")
                self._thread.start()
        return {"ok": True, "active": True, "client": self.client, "telemetry": self.telemetry_client, "mode": self.mode}

    def stop(self) -> dict:
        with self._lock:
            self.active = False
            self._stop.set()
        return {"ok": True, "active": False}

    def ping(self) -> dict:
        self.last_ping = time.monotonic()
        return {"ok": True, "active": self.active}

    def status(self) -> dict:
        return {
            "enabled": self.enabled,
            "active": self.active,
            "client": self.client,
            "telemetry_client": self.telemetry_client,
            "mode": self.mode,
            "last_ping_age_s": round(time.monotonic() - self.last_ping, 2) if self.last_ping else None,
        }

    def _loop(self) -> None:
        video_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        telemetry_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        last_tel = 0.0
        while not self._stop.is_set():
            if not self.active or not self.client:
                time.sleep(0.05)
                continue
            if time.monotonic() - self.last_ping > self.client_timeout_s:
                self.active = False
                continue
            try:
                frame = self.camera.last_jpeg() or self.camera.capture_jpeg()
                if frame:
                    self._send_frame(video_sock, frame, self.client)
                if self.telemetry_client and time.monotonic() - last_tel > self.telemetry_interval_s:
                    payload = json.dumps(self.telemetry.full()).encode("utf-8")
                    telemetry_sock.sendto(payload, self.telemetry_client)
                    last_tel = time.monotonic()
            except Exception:
                time.sleep(0.05)

    def _send_frame(self, sock: socket.socket, frame: bytes, client: Tuple[str, int]) -> None:
        self.frame_id = (self.frame_id + 1) & 0xFFFF
        count = max(1, (len(frame) + self.payload_size - 1) // self.payload_size)
        for idx in range(count):
            chunk = frame[idx * self.payload_size:(idx + 1) * self.payload_size]
            # Equivalente al header C packed: magic, frameId, packetIndex, packetCount, payloadSize
            header = struct.pack("!HHHHH", MAGIC, self.frame_id, idx, count, len(chunk))
            sock.sendto(header + chunk, client)
