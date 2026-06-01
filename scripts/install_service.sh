#!/bin/bash
# Скрипт установки systemd сервиса iTEMPO
# Запускать: sudo bash scripts/install_service.sh

set -e

SERVICE_NAME="itempo"
SERVICE_FILE="itempo.service"
SYSTEMD_DIR="/etc/systemd/system"
PROJECT_DIR="/home/administrator/iTEMPO_test"

echo "=== Установка сервиса ${SERVICE_NAME} ==="

# Проверка существования файла сервиса
if [ ! -f "${PROJECT_DIR}/${SERVICE_FILE}" ]; then
    echo "ОШИБКА: Файл ${SERVICE_FILE} не найден в ${PROJECT_DIR}"
    exit 1
fi

# Копирование сервиса
echo "Копирование ${SERVICE_FILE} в ${SYSTEMD_DIR}/"
sudo cp "${PROJECT_DIR}/${SERVICE_FILE}" "${SYSTEMD_DIR}/${SERVICE_NAME}.service"

# Создание директорий для логов если нет
sudo mkdir -p "${PROJECT_DIR}/logs"

# Перезагрузка systemd
echo "Перезагрузка systemd..."
sudo systemctl daemon-reload

# Включение и запуск сервиса
echo "Включение автозапуска..."
sudo systemctl enable "${SERVICE_NAME}.service"

echo "Запуск сервиса..."
sudo systemctl start "${SERVICE_NAME}.service"

echo ""
echo "=== Сервис ${SERVICE_NAME} установлен ==="
echo ""
echo "Проверить статус:  sudo systemctl status ${SERVICE_NAME}"
echo "Посмотреть логи:    sudo journalctl -u ${SERVICE_NAME} -f"
echo "Остановить:         sudo systemctl stop ${SERVICE_NAME}"
echo "Перезапустить:      sudo systemctl restart ${SERVICE_NAME}"
echo "Отключить автозапуск: sudo systemctl disable ${SERVICE_NAME}"
