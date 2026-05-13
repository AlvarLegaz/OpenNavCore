"""Driver de Camera Module 3 para Raspberry Pi usando Picamera2.

Sustituye al driver camera_driver_OV2640 del ESP32.
"""
from __future__ import annotations

import io
import threading
import time
from typing import Generator, Optional

try:
    from picamera2 import Picamera2
    from picamera2.encoders import JpegEncoder
    from picamera2.outputs import FileOutput
except Exception:  # pragma: no cover
    Picamera2 = None


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame: Optional[bytes] = None
        self.condition = threading.Condition()

    def write(self, buf):
        with self.condition:
            self.frame = bytes(buf)
            self.condition.notify_all()
        return len(buf)


class CameraModule3:
    def __init__(self, high_size=(1280, 720), low_size=(640, 360), high_fps=10, low_fps=12, jpeg_quality_high=80, jpeg_quality_low=65):
        self.high_size = high_size
        self.low_size = low_size
        self.high_fps = high_fps
        self.low_fps = low_fps
        self.jpeg_quality_high = jpeg_quality_high
        self.jpeg_quality_low = jpeg_quality_low
        self._lock = threading.RLock()
        self._picam2 = None
        self._output: Optional[StreamingOutput] = None
        self._mode = "low"
        self.error: Optional[str] = None

    def start(self) -> None:
        if Picamera2 is None:
            self.error = "Falta Picamera2. En Raspberry instala python3-picamera2."
            return
        with self._lock:
            self._picam2 = Picamera2()
            self._configure_video("low")
            self.error = None

    @property
    def ok(self) -> bool:
        return self._picam2 is not None and self.error is None

    @property
    def mode(self) -> str:
        return self._mode

    def _configure_video(self, mode: str) -> None:
        if not self._picam2:
            return
        size = self.high_size if mode == "high" else self.low_size
        fps = self.high_fps if mode == "high" else self.low_fps
        quality = self.jpeg_quality_high if mode == "high" else self.jpeg_quality_low

        try:
            self._picam2.stop_recording()
        except Exception:
            pass
        try:
            self._picam2.stop()
        except Exception:
            pass

        config = self._picam2.create_video_configuration(
            main={"size": size},
            controls={"FrameRate": float(fps)},
            buffer_count=2 if mode == "low" else 3,
        )
        self._picam2.configure(config)
        self._picam2.start()
        time.sleep(0.25)
        self._output = StreamingOutput()
        encoder = JpegEncoder(q=quality)
        self._picam2.start_recording(encoder, FileOutput(self._output))
        self._mode = mode

    def set_mode(self, mode: str) -> None:
        if mode not in ("low", "high"):
            mode = "low"
        with self._lock:
            if self._mode != mode:
                self._configure_video(mode)

    def capture_jpeg(self, quality: int = 85) -> bytes:
        if not self._picam2:
            raise RuntimeError(self.error or "Cámara no inicializada")
        # Usamos el último frame JPEG del stream. Es rápido y evita reconfigurar.
        with self._output.condition:
            self._output.condition.wait(timeout=2.0)
            frame = self._output.frame
        if not frame:
            raise RuntimeError("No hay frame disponible")
        return frame

    def mjpeg_frames(self, mode: str = "low") -> Generator[bytes, None, None]:
        if not self._picam2:
            raise RuntimeError(self.error or "Cámara no inicializada")
        self.set_mode("high" if mode == "high" else "low")
        while True:
            with self._output.condition:
                self._output.condition.wait(timeout=2.0)
                frame = self._output.frame
            if not frame:
                continue
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n"
                b"Content-Length: " + str(len(frame)).encode() + b"\r\n\r\n" +
                frame + b"\r\n"
            )

    def last_jpeg(self) -> Optional[bytes]:
        if not self._output:
            return None
        return self._output.frame

    def status(self) -> dict:
        return {"ok": self.ok, "mode": self.mode, "error": self.error, "high_size": self.high_size, "low_size": self.low_size}
