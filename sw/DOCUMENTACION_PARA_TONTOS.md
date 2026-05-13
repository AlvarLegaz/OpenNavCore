# Rover Raspberry Pi - Documentación para tontos

Esta carpeta es una versión para **Raspberry Pi** del proyecto original hecho para **ESP32-CAM**.

La idea es que el rover haga lo mismo que antes:

- Ver vídeo en directo desde el navegador.
- Sacar una foto JPEG.
- Leer GPS.
- Leer IMU MPU9250.
- Leer BMP280.
- Encender y apagar luces.
- Dar telemetría en JSON.
- Enviar vídeo/telemetría por UDP si lo necesitas.

Pero ahora usando una **Raspberry Pi + Camera Module 3**.

---

## 1. Qué necesitas

### Hardware

Necesitas esto:

- Raspberry Pi con Raspberry Pi OS.
- Raspberry Pi Camera Module 3 conectada por CSI.
- GPS por UART.
- MPU9250 por I2C.
- BMP280 por I2C.
- Un LED, relé o driver de luces conectado a un GPIO.

### Conexiones recomendadas

#### Cámara

La Camera Module 3 va al conector CSI de la Raspberry con su cable plano.

No va a GPIO. No va a USB. Va al conector de cámara.

#### I2C para MPU9250 y BMP280

En Raspberry Pi normalmente se usa:

| Señal | GPIO BCM | Pin físico |
|---|---:|---:|
| SDA | GPIO2 | Pin 3 |
| SCL | GPIO3 | Pin 5 |
| 3.3V | - | Pin 1 |
| GND | - | Pin 6 |

Importante: usa **3.3V**, no 5V, salvo que tu módulo soporte 5V claramente.

#### GPS UART

En Raspberry Pi normalmente se usa:

| Señal GPS | Raspberry |
|---|---|
| TX del GPS | RX Raspberry GPIO15, pin físico 10 |
| RX del GPS | TX Raspberry GPIO14, pin físico 8 |
| GND | GND |
| VCC | según tu GPS, normalmente 3.3V o 5V |

Ojo: TX va con RX y RX va con TX.

#### Luces

Por defecto este proyecto usa:

| Función | GPIO BCM | Pin físico |
|---|---:|---:|
| Luces | GPIO17 | Pin 11 |

No conectes luces potentes directamente al GPIO. Usa transistor, MOSFET, relé o driver.

---

## 2. Qué archivo tocar si algo cambia

Casi todo se cambia en:

```bash
config.py
```

Ahí puedes cambiar:

- Puerto del GPS.
- Velocidad del GPS.
- Pin de luces.
- Resolución de cámara.
- FPS.
- Puerto del servidor.
- Direcciones I2C.

Ejemplo:

```python
lights_pin: int = 17
port: str = "/dev/serial0"
baudrate: int = 9600
```

---

## 3. Instalación desde cero

Copia la carpeta `rover_rpi` a tu Raspberry.

Por ejemplo, que quede así:

```bash
/home/pi/rover_rpi
```

Entra en la carpeta:

```bash
cd /home/pi/rover_rpi
```

Ejecuta el instalador:

```bash
chmod +x install.sh
./install.sh
```

Si algo falla, lee el mensaje. Normalmente será porque falta internet, porque no estás en Raspberry Pi OS, o porque la cámara no está bien conectada.

---

## 4. Activar I2C

Ejecuta:

```bash
sudo raspi-config
```

Entra en:

```text
Interface Options -> I2C -> Enable
```

Reinicia:

```bash
sudo reboot
```

---

## 5. Probar la cámara antes del proyecto

Antes de culpar al código, prueba que la cámara funciona.

Ejecuta:

```bash
rpicam-hello
```

Si ves imagen, bien.

Prueba una foto:

```bash
rpicam-still -o prueba.jpg
```

Si esto falla, el problema es de cámara/cable/sistema, no del proyecto.

---

## 6. Probar I2C

Ejecuta:

```bash
i2cdetect -y 1
```

Deberías ver algo como:

- `68` para MPU9250.
- `76` o `77` para BMP280.

Si no sale nada, revisa cables SDA/SCL, alimentación y GND.

---

## 7. Probar el GPS

El GPS está configurado por defecto en:

```text
/dev/serial0
9600 baudios
```

Puedes mirar si llegan datos con:

```bash
sudo apt install -y minicom
minicom -b 9600 -D /dev/serial0
```

Deberías ver líneas raras que empiezan por `$GP...` o `$GN...`.

Ejemplo:

```text
$GPRMC,...
$GNGLL,...
```

Si no ves nada:

- Revisa TX/RX cruzados.
- Revisa alimentación.
- Revisa que el GPS tenga cielo o esté cerca de una ventana.
- Revisa que el puerto sea `/dev/serial0`.

---

## 8. Arrancar el servidor a mano

Entra en la carpeta:

```bash
cd /home/pi/rover_rpi
```

Activa el entorno:

```bash
source .venv/bin/activate
```

Arranca:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000
```

Ahora abre en tu navegador:

```text
http://IP_DE_TU_RASPBERRY:8000
```

Ejemplo:

```text
http://192.168.1.50:8000
```

---

## 9. Endpoints disponibles

### Página principal

```text
/
/info
```

Abre el panel web básico.

### Telemetría completa

```text
/telemetry
```

Devuelve GPS + IMU + sistema.

### Sistema

```text
/system
```

Devuelve temperatura, uptime y datos básicos.

### GPS

```text
/gps
```

Devuelve latitud, longitud, velocidad, rumbo, satélites y hora UTC.

### IMU

```text
/imu
```

Devuelve roll, pitch, yaw, altitud, presión y temperatura.

### Foto

```text
/capture
```

Devuelve una imagen JPEG.

### Vídeo alta calidad

```text
/stream
```

MJPEG en alta calidad.

### Vídeo baja latencia

```text
/stream_low
```

MJPEG en baja resolución.

### Luces

```text
/luces/on
/luces/off
```

Enciende y apaga el GPIO de luces.

### UDP

```text
/udp/start
/udp/stop
/udp/status
/udp/ping
```

Ejemplo:

```text
/udp/start?ip=192.168.1.100&port=4210&telemetry_port=4211&mode=low
```

---

## 10. Instalar como servicio automático

Esto sirve para que el rover arranque solo cuando enciendes la Raspberry.

Primero asegúrate de que el proyecto está en:

```text
/home/pi/rover_rpi
```

Copia el servicio:

```bash
sudo cp systemd/rover.service /etc/systemd/system/rover.service
```

Recarga systemd:

```bash
sudo systemctl daemon-reload
```

Activa el servicio:

```bash
sudo systemctl enable rover.service
```

Arráncalo:

```bash
sudo systemctl start rover.service
```

Ver estado:

```bash
sudo systemctl status rover.service
```

Ver logs:

```bash
journalctl -u rover.service -f
```

Pararlo:

```bash
sudo systemctl stop rover.service
```

---

## 11. Qué significa cada archivo

### `main.py`

Es el servidor web.

Aquí están las rutas:

- `/telemetry`
- `/gps`
- `/imu`
- `/capture`
- `/stream`
- `/luces/on`
- etc.

### `camera_module3.py`

Controla la Camera Module 3.

Hace dos cosas importantes:

- Capturar JPEG.
- Generar stream MJPEG.

Este archivo sustituye al antiguo driver `camera_driver_OV2640.cpp`.

### `gps.py`

Lee el GPS por UART.

Entiende frases NMEA como:

- GPRMC
- GNGLL
- GPGSV

### `imu.py`

Lee el MPU9250 y el BMP280.

El yaw es relativo. Esto significa que puede derivar con el tiempo. No es una brújula perfecta.

### `telemetry.py`

Junta todos los datos y los convierte en JSON.

### `gpio_control.py`

Controla las luces.

### `udp_stream.py`

Envía JPEG por UDP troceado en paquetes.

### `config.py`

Archivo de configuración principal.

### `static/`

Páginas HTML sencillas.

### `systemd/rover.service`

Servicio para arranque automático.

---

## 12. Diferencias importantes con el ESP32

En ESP32 usabas:

- FreeRTOS.
- `esp_camera`.
- `WebServer`.
- `WiFi`.
- `Preferences`.

En Raspberry usamos:

- Linux.
- Python.
- FastAPI.
- Picamera2.
- systemd.
- UART/I2C normales de Linux.

No es una copia línea por línea. Es un port funcional: intenta comportarse igual desde fuera.

---

## 13. Problemas típicos

### No se ve la cámara

Prueba:

```bash
rpicam-hello
```

Si falla:

- Revisa cable plano.
- Revisa orientación del cable.
- Reinicia.
- Actualiza Raspberry Pi OS.

### `/capture` dice que no hay cámara

Seguramente falta Picamera2 o no estás ejecutando en Raspberry Pi OS.

Prueba:

```bash
python3 -c "from picamera2 import Picamera2; print('ok')"
```

### No aparece el MPU9250

Prueba:

```bash
i2cdetect -y 1
```

Si no ves `68`, revisa cables.

### No aparece el BMP280

Busca `76` o `77` en:

```bash
i2cdetect -y 1
```

Si no aparece, revisa alimentación y SDA/SCL.

### GPS sin fix

Es normal al principio.

El GPS puede tardar varios minutos en coger señal, sobre todo dentro de casa.

### Las luces no se encienden

Revisa:

- Que estés usando GPIO BCM 17, no pin físico 17.
- Que el GND sea común.
- Que no estés conectando demasiada carga directa al GPIO.

---

## 14. Orden recomendado para ponerlo en marcha

Hazlo así:

1. Arranca Raspberry Pi OS.
2. Conecta la Camera Module 3.
3. Prueba `rpicam-hello`.
4. Activa I2C.
5. Prueba `i2cdetect -y 1`.
6. Prueba el GPS con `minicom`.
7. Ejecuta `./install.sh`.
8. Arranca `uvicorn main:app --host 0.0.0.0 --port 8000`.
9. Abre `http://IP_DE_TU_RASPBERRY:8000`.
10. Cuando funcione, instala el servicio systemd.

---

## 15. Estado actual del port

Esta es una **primera versión funcional**.

Está preparada para arrancar y mantener la misma idea del proyecto original, pero puede necesitar ajustes en hardware real:

- Dirección exacta del BMP280.
- Puerto GPS.
- Pin de luces.
- Resolución/FPS de cámara.
- Usuario de systemd si no usas `pi`.

No te asustes si algo no funciona a la primera. En robótica casi nunca funciona a la primera.

---

## 16. Comando mágico para arrancar rápido

Si ya instalaste todo:

```bash
cd /home/pi/rover_rpi
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

Y abre:

```text
http://IP_DE_TU_RASPBERRY:8000
```

FIN.
