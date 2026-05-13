# Rover Raspberry Pi

Port funcional del rover ESP32-CAM a Raspberry Pi + Camera Module 3.

Lee primero:

```text
DOCUMENTACION_PARA_TONTOS.md
```

## Arranque rápido

```bash
cd /home/pi/rover_rpi
chmod +x install.sh
./install.sh
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Abre:

```text
http://IP_DE_TU_RASPBERRY:8000
```

## Endpoints principales

- `/info`
- `/telemetry`
- `/system`
- `/gps`
- `/imu`
- `/capture`
- `/stream`
- `/stream_low`
- `/luces/on`
- `/luces/off`
- `/udp/start`
- `/udp/stop`
- `/udp/status`
- `/udp/ping`


