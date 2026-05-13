from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

import config
from camera_module3 import CameraModule3
from gpio_control import GPIOControl
from gps import GPSReader
from imu import IMUReader
from telemetry import Telemetry
from udp_stream import UDPStreamer

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Rover Raspberry Pi", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

camera = CameraModule3(
    high_size=config.CAMERA.high_size,
    low_size=config.CAMERA.low_size,
    high_fps=config.CAMERA.high_fps,
    low_fps=config.CAMERA.low_fps,
    jpeg_quality_high=config.CAMERA.jpeg_quality_high,
    jpeg_quality_low=config.CAMERA.jpeg_quality_low,
)
gps = GPSReader(config.GPS.port, config.GPS.baudrate, config.GPS.enabled)
imu = IMUReader(config.I2C.bus, config.I2C.mpu9250_addr, config.I2C.bmp280_addr_candidates, config.I2C.sea_level_hpa, config.I2C.enabled)
gpio = GPIOControl(config.GPIO.lights_pin, config.GPIO.enabled)
telemetry = Telemetry(gps, imu)
udp = UDPStreamer(camera, telemetry, config.UDP.video_payload_size, config.UDP.telemetry_interval_s, config.UDP.client_timeout_s, config.UDP.enabled)


@app.on_event("startup")
def startup() -> None:
    camera.start()
    gps.start()
    imu.start()
    gpio.start()


@app.get("/", response_class=HTMLResponse)
def root():
    return FileResponse(STATIC_DIR / "info.html")


@app.get("/info", response_class=HTMLResponse)
def info():
    return FileResponse(STATIC_DIR / "info.html")


@app.get("/config", response_class=HTMLResponse)
def config_page():
    return FileResponse(STATIC_DIR / "config.html")


@app.post("/save")
async def save_config_placeholder(request: Request):
    # En ESP32 guardabas WiFi en flash. En Raspberry se recomienda NetworkManager.
    form = await request.form()
    return JSONResponse({"ok": False, "message": "Config web recibida, pero WiFi se configura en Raspberry con NetworkManager.", "received": dict(form)})


@app.get("/telemetry")
def telemetry_full():
    return JSONResponse(telemetry.full())


@app.get("/system")
def system():
    return JSONResponse(telemetry.system())


@app.get("/gps")
def gps_json():
    data = telemetry.gps_json()
    if gps.error:
        data["error"] = gps.error
    return JSONResponse(data)


@app.get("/imu")
def imu_json():
    return JSONResponse(telemetry.imu_json())


@app.get("/luces/on", response_class=PlainTextResponse)
def lights_on():
    return gpio.on()


@app.get("/luces/off", response_class=PlainTextResponse)
def lights_off():
    return gpio.off()


@app.get("/gpio")
def gpio_status():
    return JSONResponse(gpio.status())


@app.get("/camera/status")
def camera_status():
    return JSONResponse(camera.status())


@app.get("/capture")
def capture():
    try:
        frame = camera.capture_jpeg()
        return Response(content=frame, media_type="image/jpeg", headers={"Cache-Control": "no-store", "Content-Disposition": "inline; filename=capture.jpg"})
    except Exception as exc:
        return PlainTextResponse(f"Error capturando imagen: {exc}", status_code=503)


@app.get("/stream")
def stream():
    try:
        return StreamingResponse(camera.mjpeg_frames("high"), media_type="multipart/x-mixed-replace; boundary=frame")
    except Exception as exc:
        return PlainTextResponse(f"Cámara no disponible: {exc}", status_code=503)


@app.get("/stream_low")
def stream_low():
    try:
        return StreamingResponse(camera.mjpeg_frames("low"), media_type="multipart/x-mixed-replace; boundary=frame")
    except Exception as exc:
        return PlainTextResponse(f"Cámara no disponible: {exc}", status_code=503)


@app.get("/udp/start")
def udp_start(request: Request, ip: Optional[str] = Query(default=None), port: int = 4210, telemetry_port: int = 4211, mode: str = "low"):
    client_ip = ip or request.client.host
    return JSONResponse(udp.start(client_ip, port, telemetry_port, mode))


@app.get("/udp/stop")
def udp_stop():
    return JSONResponse(udp.stop())


@app.get("/udp/status")
def udp_status():
    return JSONResponse(udp.status())


@app.get("/udp/ping")
def udp_ping():
    return JSONResponse(udp.ping())
