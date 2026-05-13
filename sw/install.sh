#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "== Rover Raspberry Pi: instalación =="
echo "Actualizando paquetes..."
sudo apt update

echo "Instalando dependencias del sistema..."
sudo apt install -y python3-venv python3-pip python3-picamera2 i2c-tools python3-libcamera python3-kms++

echo "Creando entorno virtual..."
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Activando I2C y cámara desde raspi-config si aún no lo hiciste:"
echo "  sudo raspi-config"
echo "  Interface Options -> I2C -> Enable"
echo "La cámara CSI suele estar activa automáticamente en Raspberry Pi OS moderno."

echo "Instalación terminada. Arranca con:"
echo "  source .venv/bin/activate"
echo "  uvicorn main:app --host 0.0.0.0 --port 8000"
