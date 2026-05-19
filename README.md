# OpenNavCore

**OpenNavCore** es una arquitectura modular para sistemas autónomos, pensada para servir como base común en rovers, drones, vehículos submarinos, barcos autónomos y plataformas robóticas experimentales.

El proyecto nace como evolución de un sistema de telemetría y vídeo para rover, pero está diseñado para no depender de un único tipo de vehículo. La idea principal es separar claramente el control del hardware de la comunicación con el exterior.

---
## Arrancar el servidor a mano

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

## Idea principal

OpenNavCore está formado por dos módulos principales:

1. **Control Core**
2. **Gateway Core**

```text
┌──────────────────────────────────────────────┐
│                  OpenNavCore                   │
├──────────────────────┬───────────────────────┤
│     Control Core     │     Gateway Core      │
├──────────────────────┼───────────────────────┤
│ Sensores             │ API REST              │
│ Actuadores           │ Servidor web          │
│ Motores              │ Streaming de vídeo    │
│ IMU / GPS / barómetro│ Telemetría JSON       │
│ Seguridad / failsafe │ UDP / WebSocket       │
│ Modos de control     │ Configuración remota  │
└──────────────────────┴───────────────────────┘
```

En pocas palabras:

```text
OpenNavCore = Control Core + Gateway Core
```

---

## ¿Qué es el Control Core?

El **Control Core** es el módulo encargado de interactuar directamente con el hardware del sistema autónomo.

Es la parte que lee sensores, controla actuadores y mantiene el estado interno del vehículo.

### Responsabilidades principales

- Lectura de sensores.
- Control de motores, servos, luces o relés.
- Gestión de GPS.
- Gestión de IMU.
- Lectura de barómetro, temperatura, presión o profundidad.
- Control de batería y alimentación.
- Generación de telemetría.
- Control manual o autónomo.
- Gestión de modos de operación.
- Sistemas de seguridad.
- Watchdog y failsafe.

### Ejemplos de hardware gestionado

- GPS.
- IMU.
- Barómetro.
- Cámara.
- Sensor de profundidad.
- Sensores de distancia.
- Motores DC.
- ESC.
- Servos.
- Relés.
- Luces.
- Batería.
- Sensores ambientales.

---

## ¿Qué es el Gateway Core?

El **Gateway Core** es el módulo encargado de comunicar OpenNavCore con el exterior.

Actúa como puente entre el sistema autónomo y el usuario, estación base, navegador web, API externa o red de comunicaciones.

### Responsabilidades principales

- Servidor web.
- API REST.
- Streaming de cámara.
- Telemetría en tiempo real.
- Comunicación UDP.
- Comunicación WebSocket.
- Panel de control.
- Configuración remota.
- Logs.
- Diagnóstico.
- Envío de datos a estación base.
- Integración futura con otros sistemas.

### Ejemplos de funciones

- Ver vídeo en directo.
- Consultar GPS.
- Consultar sensores.
- Activar luces.
- Cambiar modos de operación.
- Enviar comandos manuales.
- Descargar logs.
- Supervisar estado del sistema.
- Conectar con una estación de control.

---

## Objetivo del proyecto

El objetivo de OpenNavCore es crear una base reutilizable para sistemas autónomos.

No está pensado únicamente para un rover. La misma arquitectura puede adaptarse a distintos tipos de plataformas:

| Plataforma | Ejemplo de uso |
|---|---|
| Rover terrestre | Exploración, vigilancia, telemetría, navegación |
| Drone / UAV | Vuelo asistido, streaming, telemetría, misiones |
| Submarino / ROV | Profundidad, sensores, cámara, control remoto |
| Barco autónomo | Navegación, GPS, sensores ambientales |
| Robot experimental | Pruebas de sensores, visión artificial, control |

---

## Filosofía de diseño

OpenNavCore sigue una filosofía modular:

- Separar control y comunicación.
- Evitar depender de un único vehículo.
- Mantener APIs simples.
- Facilitar la depuración.
- Permitir crecimiento progresivo.
- Usar componentes reemplazables.
- Priorizar estabilidad antes que complejidad.
- Mantener una estructura clara para humanos.

---

## Estructura recomendada del repositorio

```text
OpenNavCore/
├── control/
│   ├── sensors/
│   ├── actuators/
│   ├── navigation/
│   ├── safety/
│   └── telemetry/
│
├── gateway/
│   ├── api/
│   ├── web/
│   ├── video/
│   ├── udp/
│   └── websocket/
│
├── shared/
│   ├── models/
│   ├── config/
│   └── utils/
│
├── platforms/
│   ├── rover/
│   ├── drone/
│   ├── submarine/
│   └── generic/
│
├── docs/
├── examples/
├── scripts/
└── README.md
```

---

## Arquitectura lógica

```text
Usuario / Estación base / Navegador
                  │
                  ▼
           ┌──────────────┐
           │ Gateway Core │
           └──────┬───────┘
                  │
                  ▼
           ┌──────────────┐
           │ Control Core │
           └──────┬───────┘
                  │
                  ▼
       Sensores / Actuadores / Vehículo
```

---

## Ejemplo de flujo de datos

### Telemetría

```text
Sensores
  ↓
Control Core
  ↓
Telemetry Snapshot
  ↓
Gateway Core
  ↓
API REST / WebSocket / UDP
  ↓
Usuario o estación base
```

### Vídeo

```text
Cámara
  ↓
Control Core o módulo de cámara
  ↓
Gateway Core
  ↓
MJPEG / WebRTC / UDP / HTTP
  ↓
Panel de control
```

### Comando remoto

```text
Usuario pulsa un botón
  ↓
Gateway Core recibe el comando
  ↓
Control Core valida la acción
  ↓
Actuador ejecuta el comando
  ↓
Telemetry confirma el nuevo estado
```

---

## Endpoints previstos

Una implementación inicial de OpenNavCore puede exponer endpoints como:

```text
GET  /
GET  /info
GET  /system
GET  /telemetry
GET  /gps
GET  /imu
GET  /capture
GET  /stream
GET  /stream_low

POST /control/mode
POST /control/command
POST /actuators/lights/on
POST /actuators/lights/off

POST /udp/start
POST /udp/stop
GET  /udp/status
GET  /udp/ping
```

---

## Posibles modos de operación

OpenNavCore puede soportar varios modos:

| Modo | Descripción |
|---|---|
| Manual | El usuario controla directamente el sistema |
| Asistido | El sistema ayuda, estabiliza o limita acciones peligrosas |
| Autónomo | El sistema toma decisiones según misión o sensores |
| Seguridad | Modo reducido ante error, batería baja o pérdida de señal |
| Diagnóstico | Modo para pruebas, logs y comprobación de hardware |

---

## Failsafe y seguridad

Un sistema autónomo debe estar preparado para fallos.

OpenNavCore debería contemplar:

- Pérdida de comunicación.
- Batería baja.
- Sensor no disponible.
- GPS sin fix.
- Cámara no detectada.
- Temperatura excesiva.
- Bloqueo del proceso principal.
- Comando inválido.
- Error en actuadores.
- Reinicio automático del servicio.

Ejemplo de comportamiento failsafe:

```text
Si se pierde comunicación:
  1. Detener motores.
  2. Mantener telemetría activa si es posible.
  3. Activar modo seguro.
  4. Registrar el evento.
  5. Esperar reconexión.
```

---

## Plataforma inicial

La primera implementación práctica puede usar:

- Raspberry Pi.
- Raspberry Pi Camera Module 3.
- GPS por UART.
- Sensores I2C.
- IMU MPU9250 o equivalente.
- BMP280/BME280.
- Python 3.
- FastAPI o Flask.
- Picamera2.
- systemd.

---

## Futuras ampliaciones

Ideas para versiones futuras:

- Soporte para ROS 2.
- WebSocket en tiempo real.
- Control de motores.
- Planificador de misiones.
- Modo autónomo básico.
- Grabación de vídeo.
- Logs persistentes.
- Integración con mapas.
- Detección de objetos con OpenCV.
- Soporte para LIDAR.
- Soporte para sonar.
- Soporte para sensor de profundidad.
- Control PID.
- Perfiles por plataforma.
- Panel web avanzado.
- Aplicación móvil.
- Comunicación LoRa.
- Comunicación 4G/5G.
- Integración con MAVLink.

---

## Lema

```text
A modular brain for autonomous exploration.
```

O en español:

```text
Un núcleo modular para máquinas autónomas.
```

---

## Estado del proyecto

OpenNavCore está en fase inicial de diseño y prototipado.

La prioridad inicial es crear una base estable con:

- Cámara.
- Telemetría.
- GPS.
- IMU.
- API REST.
- Streaming.
- Control básico de actuadores.
- Servicio automático en Linux.

---

## Resumen corto

**OpenNavCore** es un núcleo modular para sistemas autónomos compuesto por un **Control Core** para sensores, actuadores y seguridad, y un **Gateway Core** para comunicación, telemetría, vídeo y supervisión remota.

Está pensado para crecer desde un rover inicial hacia una plataforma común para vehículos terrestres, aéreos, acuáticos y submarinos.
