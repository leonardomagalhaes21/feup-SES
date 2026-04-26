.PHONY: install scan test help pre-commit

TARGET ?= ./target

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

install: ## Install project dependencies
	uv sync

scan: ## Run security scan (TARGET=./path to override)
	uv run python gatekeeper.py scan --target $(TARGET)

test: ## Run unit tests
	uv run pytest tests/ -v

pre-commit: ## Install pre-commit hooks
	uv run pre-commit install


