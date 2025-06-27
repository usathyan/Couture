# Makefile for the Couture bookkeeping project

# Define executables from the virtual environment for robustness
VENV_PYTHON = .venv/bin/python3
VENV_RUFF = .venv/bin/ruff
VENV_PYRIGHT = .venv/bin/pyright
VENV_PYTEST = .venv/bin/pytest
VENV_UVICORN = .venv/bin/uvicorn

# Default target
all: install

# Install dependencies into the uv-managed venv
install:
	@echo "Installing dependencies..."
	uv pip install -r requirements.txt

# Lint the code using direct executable paths
lint:
	@echo "Linting code..."
	@echo "Running ruff..."
	$(VENV_RUFF) check .
	@echo "Running pyright..."
	$(VENV_PYRIGHT) src

# Run the application locally
run:
	@echo "Starting application..."
	$(VENV_UVICORN) src.main:app --host 0.0.0.0 --port 8080 --reload

# Run tests
test: lint
	@echo "Running tests..."
	$(VENV_PYTEST)

.PHONY: all install lint run test
