# Documentación avanzada — Rover Raspberry Pi Port

Esta documentación es la referencia técnica del port del rover desde ESP32-CAM a Raspberry Pi.

El objetivo de este proyecto no es traducir el firmware Arduino línea por línea, sino conservar el comportamiento funcional del sistema original: vídeo, captura, telemetría, sensores, GPS, GPIO, API HTTP y emisión UDP.

---

## 1. Resumen de arquitectura

El proyecto está dividido en módulos independientes:

```text
rover_rpi/
├── main.py                  # API HTTP principal
├── camera_module3.py        # Camera Module 3 / Picamera2
├── gps.py                   # GPS UART + parser NMEA básico
├── imu.py                   # MPU9250 + BMP280 por I2C
├── telemetry.py             # Snapshot unificado de telemetría
├── gpio_control.py          # Control de luces / GPIO
├── udp_stream.py            # Emisión UDP de vídeo y telemetría
├── config.py                # Configuración central
├── requirements.txt         # Dependencias Python
├── install.sh               # Instalador básico
├── systemd/rover.service    # Servicio systemd
├── static/                  # Páginas HTML
└── tools/                   # Herramientas de prueba
```

La Raspberry ejecuta un servicio Python que arranca:

1. Cámara.
2. GPS.
3. IMU/barómetro.
4. Telemetría.
5. API web.
6. Servicios UDP bajo demanda.

---

## 2. Diferencias importantes frente al ESP32

### ESP32 original

El proyecto original usaba:

- Arduino framework.
- `WebServer` embebido.
- `esp_camera`.
- FreeRTOS.
- Watchdog ESP32.
- WiFi AP/STA gestionado desde firmware.
- Memoria flash para configuración.

### Raspberry Pi

El port usa:

- Linux.
- Python 3.
- FastAPI/Uvicorn.
- Picamera2/libcamera.
- Threads de Python.
- `systemd` para arranque y reinicio.
- Red gestionada por Raspberry Pi OS.
- Archivos de configuración o variables en `config.py`.

No existe una equivalencia directa de algunas APIs del ESP32. Por eso el port es funcional, no literal.

---

## 3. Flujo general de ejecución

Cuando se ejecuta `main.py`:

1. Se cargan los valores de `config.py`.
2. Se inicializa el controlador GPIO.
3. Se intenta inicializar la cámara.
4. Se arranca el hilo del GPS.
5. Se arranca el hilo de sensores IMU/BMP280.
6. Se arranca el agregador de telemetría.
7. Uvicorn expone la API HTTP.

El flujo simplificado es:

```text
          ┌──────────────┐
          │   main.py    │
          └──────┬───────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
 camera      telemetry       API HTTP
    │            │            │
 capture     GPS + IMU       endpoints
 stream      BMP280          JSON/HTML
```

---

## 4. API HTTP

Por defecto el servidor escucha en:

```text
http://0.0.0.0:8000
```

Desde otro dispositivo en la misma red:

```text
http://IP_DE_LA_RASPBERRY:8000
```

### Endpoints principales

| Endpoint | Método | Descripción |
|---|---:|---|
| `/` | GET | Página principal / redirección simple |
| `/info` | GET | Página de información |
| `/config` | GET | Página de configuración básica |
| `/telemetry` | GET | JSON completo de telemetría |
| `/system` | GET | Estado del sistema |
| `/gps` | GET | Datos GPS |
| `/imu` | GET | Datos IMU/BMP280 |
| `/capture` | GET | Captura JPEG |
| `/stream` | GET | Stream MJPEG normal |
| `/stream_low` | GET | Stream MJPEG baja latencia |
| `/luces/on` | GET/POST | Enciende luces |
| `/luces/off` | GET/POST | Apaga luces |
| `/udp/start` | GET/POST | Inicia envío UDP |
| `/udp/stop` | GET/POST | Detiene envío UDP |
| `/udp/status` | GET | Estado UDP |
| `/udp/ping` | GET | Prueba simple UDP/API |

---

## 5. Cámara — Camera Module 3

### Módulo implicado

```text
camera_module3.py
```

### Backend usado

El port utiliza `Picamera2`, que a su vez usa el stack `libcamera` de Raspberry Pi OS.

### Modos implementados

El diseño separa dos modos:

| Modo | Uso | Resolución orientativa |
|---|---|---|
| Normal | `/stream`, `/capture` | 1280x720 |
| Low latency | `/stream_low` | 640x360 |

Estos valores se pueden cambiar en `config.py`.

### Captura JPEG

El endpoint `/capture` solicita un frame a la cámara, lo codifica como JPEG y lo devuelve con cabecera:

```text
Content-Type: image/jpeg
```

### MJPEG

El streaming MJPEG funciona generando una respuesta HTTP multipart:

```text
multipart/x-mixed-replace; boundary=frame
```

Cada frame se envía como:

```text
--frame
Content-Type: image/jpeg

<bytes JPEG>
```

### Puntos críticos

- La cámara solo debe ser usada por un hilo a la vez.
- El módulo usa un lock para evitar capturas simultáneas.
- Cambiar entre modo normal y low latency puede requerir parar y reconfigurar la cámara.
- Si la cámara falla al arrancar, revisar primero `rpicam-hello`.

### Pruebas manuales

```bash
rpicam-hello
rpicam-still -o test.jpg
rpicam-vid -t 5000 -o test.h264
```

Si esos comandos fallan, el problema no está en el proyecto Python sino en la configuración de cámara del sistema.

---

## 6. GPS

### Módulo implicado

```text
gps.py
```

### Puerto por defecto

Normalmente en Raspberry Pi:

```text
/dev/serial0
```

Puede variar según configuración:

```text
/dev/ttyAMA0
/dev/ttyS0
/dev/ttyUSB0
```

El puerto se configura en `config.py`.

### Baudrate típico

```text
9600
```

Algunos módulos usan:

```text
38400
57600
115200
```

### Datos leídos

El parser NMEA básico procesa frases como:

- `$GPGGA`
- `$GPRMC`
- `$GN...`

Datos típicos generados:

- latitud
- longitud
- fix válido
- número de satélites
- altitud
- velocidad
- rumbo
- timestamp

### Diagnóstico GPS

Ver si salen datos crudos:

```bash
sudo apt install -y minicom
minicom -D /dev/serial0 -b 9600
```

O:

```bash
cat /dev/serial0
```

Si no aparece nada:

1. Revisar TX/RX cruzados.
2. Revisar GND común.
3. Revisar alimentación del módulo.
4. Revisar que la consola serie de Linux esté desactivada.

---

## 7. IMU y BMP280

### Módulo implicado

```text
imu.py
```

### Bus I2C por defecto

```text
/dev/i2c-1
```

### Pines Raspberry Pi

| Señal | GPIO | Pin físico |
|---|---:|---:|
| SDA | GPIO2 | Pin 3 |
| SCL | GPIO3 | Pin 5 |
| 3.3V | - | Pin 1 o 17 |
| GND | - | Pin 6, 9, 14, etc. |

### Direcciones I2C habituales

| Dispositivo | Dirección típica |
|---|---|
| MPU9250 | `0x68` o `0x69` |
| BMP280 | `0x76` o `0x77` |

Escaneo del bus:

```bash
sudo apt install -y i2c-tools
i2cdetect -y 1
```

Si no aparece nada:

1. Revisar cableado.
2. Revisar alimentación a 3.3V.
3. Activar I2C con `sudo raspi-config`.
4. Verificar que el sensor no necesita pull-ups adicionales.

### Cálculo de orientación

El port mantiene el concepto del firmware ESP32:

- roll
- pitch
- yaw relativo
- heading si hay magnetómetro disponible
- altitud estimada desde presión

Importante: el yaw basado en giroscopio deriva con el tiempo si no se corrige con magnetómetro. Esto no es un bug, es normal en IMUs sin fusión completa.

---

## 8. Telemetría

### Módulo implicado

```text
telemetry.py
```

La telemetría actúa como capa unificada entre sensores y API.

### Patrón usado

Cada módulo mantiene su estado interno. `telemetry.py` recoge snapshots y genera un JSON único.

Ejemplo conceptual:

```json
{
  "ok": true,
  "timestamp": 1710000000.0,
  "gps": {
    "fix": true,
    "lat": 40.0,
    "lon": -3.0
  },
  "imu": {
    "roll": 0.0,
    "pitch": 0.0,
    "yaw": 0.0
  },
  "system": {
    "uptime": 123,
    "camera_ok": true
  }
}
```

### Concurrencia

La telemetría debe evitar leer estructuras mientras otro hilo las modifica. Por eso los módulos usan locks para proteger snapshots.

---

## 9. GPIO y luces

### Módulo implicado

```text
gpio_control.py
```

El pin de luces se define en `config.py`.

Ejemplo:

```python
LIGHT_GPIO = 17
```

### Consideraciones eléctricas

Nunca alimentar luces, motores o cargas grandes directamente desde un GPIO.

Usar siempre:

- transistor MOSFET
- relé con driver
- módulo relé optoacoplado
- diodo flyback si hay bobinas
- GND común

El GPIO de Raspberry es de 3.3V y no tolera 5V.

---

## 10. UDP

### Módulo implicado

```text
udp_stream.py
```

El servicio UDP está pensado para enviar:

- frames JPEG reducidos
- telemetría JSON
- estado del sistema

### Uso previsto

El cliente remoto llama a:

```text
/udp/start?host=IP_CLIENTE&port=PUERTO
```

Después la Raspberry empieza a enviar paquetes UDP hacia ese destino.

### Limitaciones

UDP no garantiza entrega ni orden. Es útil para baja latencia, pero puede perder paquetes.

Para vídeo serio en red, considerar en el futuro:

- RTSP
- WebRTC
- GStreamer
- HLS de baja latencia

---

## 11. Servicio systemd

Archivo:

```text
systemd/rover.service
```

Instalación típica:

```bash
sudo cp systemd/rover.service /etc/systemd/system/rover.service
sudo systemctl daemon-reload
sudo systemctl enable rover
sudo systemctl start rover
```

Ver estado:

```bash
systemctl status rover
```

Ver logs:

```bash
journalctl -u rover -f
```

Reiniciar:

```bash
sudo systemctl restart rover
```

Parar:

```bash
sudo systemctl stop rover
```

### Reinicio automático

El servicio puede configurarse con:

```ini
Restart=always
RestartSec=3
```

Esto sustituye en parte al watchdog del ESP32.

---

## 12. Instalador

Archivo:

```text
install.sh
```

Responsabilidades:

1. Instalar paquetes del sistema.
2. Crear entorno virtual Python.
3. Instalar dependencias de `requirements.txt`.
4. Copiar o sugerir instalación del servicio systemd.
5. Dar instrucciones finales.

### Ejecución

```bash
chmod +x install.sh
./install.sh
```

### Posibles ajustes

Dependiendo de la versión de Raspberry Pi OS, puede que `picamera2` se instale mejor con APT que con pip.

Recomendado:

```bash
sudo apt install -y python3-picamera2
```

Si `pip install picamera2` falla, no insistir: usar el paquete oficial de APT.

---

## 13. Configuración principal

Archivo:

```text
config.py
```

Ahí se definen valores como:

- host HTTP
- puerto HTTP
- resolución cámara
- calidad JPEG
- puerto GPS
- baudrate GPS
- direcciones I2C
- pin de luces
- destino UDP por defecto

Recomendación: no tocar el código de los módulos para cambiar configuración básica. Cambiar `config.py`.

---

## 14. Puesta en marcha recomendada

### Paso 1: sistema

```bash
sudo apt update
sudo apt upgrade -y
```

### Paso 2: activar interfaces

```bash
sudo raspi-config
```

Activar:

- Camera
- I2C
- Serial port hardware

Desactivar si procede:

- login shell por serial

### Paso 3: probar cámara

```bash
rpicam-hello
```

### Paso 4: probar I2C

```bash
i2cdetect -y 1
```

### Paso 5: probar GPS

```bash
cat /dev/serial0
```

### Paso 6: instalar proyecto

```bash
cd rover_rpi
chmod +x install.sh
./install.sh
```

### Paso 7: ejecutar manualmente

```bash
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Paso 8: abrir navegador

```text
http://IP_DE_LA_RASPBERRY:8000
```

---

## 15. Diagnóstico rápido

### El servidor no arranca

Ver error:

```bash
python3 main.py
```

O con Uvicorn:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### La cámara no funciona

Probar:

```bash
rpicam-hello
```

Si falla, revisar:

- cable CSI orientado correctamente
- cámara habilitada
- sistema actualizado
- compatibilidad de Raspberry Pi OS

### GPS sin datos

Probar:

```bash
cat /dev/serial0
```

Revisar:

- TX del GPS a RX de Raspberry
- RX del GPS a TX de Raspberry
- GND común
- baudrate
- consola serie desactivada

### I2C sin dispositivos

Probar:

```bash
i2cdetect -y 1
```

Revisar:

- SDA/SCL
- alimentación 3.3V
- direcciones reales
- I2C activado

### GPIO no cambia

Revisar:

- permisos
- librería GPIO instalada
- pin BCM frente a pin físico
- circuito externo

---

## 16. Seguridad y robustez

### Red

No exponer este servidor directamente a Internet. Está pensado para red local.

Si se necesita acceso remoto:

- VPN
- Tailscale
- WireGuard
- túnel seguro

### Energía

La Raspberry necesita alimentación estable. Para rover móvil, usar regulador buck de calidad.

Recomendaciones:

- 5V estables
- margen de corriente suficiente
- evitar alimentar motores desde la misma línea sin filtrado
- condensadores cerca de la Raspberry

### Apagado

Evitar cortar alimentación sin apagar. Puede corromper la tarjeta SD.

Opciones futuras:

- botón de apagado seguro
- overlay filesystem read-only
- UPS HAT
- almacenamiento industrial

---

## 17. Mejoras futuras recomendadas

### Cámara

- WebRTC para menor latencia.
- RTSP con GStreamer.
- grabación local.
- control de autofocus.
- control de exposición.
- visión artificial con OpenCV.

### Sensores

- calibración de IMU.
- filtro Madgwick o Mahony.
- compensación de magnetómetro.
- cálculo de velocidad y distancia.

### Sistema

- configuración web persistente.
- logs rotativos.
- watchdog hardware/software.
- modo AP automático.
- portal cautivo.
- autenticación básica.

### Rover

- control de motores.
- teleoperación por joystick.
- failsafe si se pierde conexión.
- parada de emergencia.
- rutas autónomas con GPS.

---

## 18. Notas para desarrollo

### Entorno virtual

Activar:

```bash
source .venv/bin/activate
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

### Formato recomendado

Instalar herramientas:

```bash
pip install black ruff pytest
```

Formatear:

```bash
black .
```

Lint:

```bash
ruff check .
```

### Pruebas

El proyecto incluye herramientas en:

```text
tools/
```

Por ejemplo:

```bash
python tools/test_gps_parser.py
```

---

## 19. Mapeo mental ESP32 → Raspberry

| ESP32 | Raspberry |
|---|---|
| `setup()` | arranque de `main.py` |
| `loop()` | servidor Uvicorn + threads |
| FreeRTOS task | `threading.Thread` |
| mutex FreeRTOS | `threading.Lock` |
| `esp_camera_fb_get()` | `Picamera2.capture_array()` / JPEG |
| `WebServer` | FastAPI |
| `Preferences` | archivo config / JSON futuro |
| `Serial2` | `/dev/serial0` con pyserial |
| `Wire` | `smbus2` / I2C Linux |
| WDT ESP32 | systemd restart/watchdog |
| WiFi AP firmware | NetworkManager/hostapd |

---

## 20. Estado del port

Esta versión debe considerarse una primera base funcional.

Probado a nivel de sintaxis, pero no validado en hardware real dentro de este entorno.

Puntos que probablemente requieran ajuste en la Raspberry real:

- puerto GPS exacto
- dirección I2C de BMP280
- dirección I2C de MPU9250
- pin GPIO de luces
- usuario del servicio systemd
- instalación concreta de Picamera2
- permisos de cámara/GPIO/I2C

