.PHONY: test lint format check service-install service-uninstall service-status service-logs service-restart

# Run tests
test:
	uv run pytest tests/

# --- Systemd Service Management ---

# Install and enable the systemd service
service-install:
	sudo bash scripts/install_service.sh

# Remove the systemd service
service-uninstall:
	sudo bash scripts/uninstall_service.sh

# Show service status
service-status:
	sudo systemctl status itempo

# Follow service logs
service-logs:
	sudo journalctl -u itempo -f

# Restart the service
service-restart:
	sudo systemctl restart itempo

# Run Ruff linter (only checks)
lint:
	uv run ruff check src scripts tests

# Run Ruff formatter and auto-fix rules
format:
	uv run ruff check --fix src scripts tests
	uv run ruff format src scripts tests

# Run all checks (format, lint, test)
check: format lint test
