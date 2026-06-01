#!/bin/bash
# Скрипт удаления systemd сервиса iTEMPO
# Запускать: sudo bash scripts/uninstall_service.sh

set -e

SERVICE_NAME="itempo"
SYSTEMD_DIR="/etc/systemd/system"

echo "=== Удаление сервиса ${SERVICE_NAME} ==="

# Остановка сервиса
echo "Остановка сервиса..."
sudo systemctl stop "${SERVICE_NAME}.service" 2>/dev/null || true

# Отключение автозапуска
echo "Отключение автозапуска..."
sudo systemctl disable "${SERVICE_NAME}.service" 2>/dev/null || true

# Удаление файла сервиса
echo "Удаление ${SYSTEMD_DIR}/${SERVICE_NAME}.service"
sudo rm -f "${SYSTEMD_DIR}/${SERVICE_NAME}.service"

# Перезагрузка systemd
echo "Перезагрузка systemd..."
sudo systemctl daemon-reload

echo ""
echo "=== Сервис ${SERVICE_NAME} удалён ==="
