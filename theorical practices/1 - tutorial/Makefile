# Detect OS
ifeq ($(OS),Windows_NT)
    # Windows settings
    PYTHON = python
    PIP = pip
    VENV = venv
    SEP = \\
    RM = - rd /s /q
    SCRIPTS = Scripts
else
    # Unix/Linux settings
    PYTHON = python3
    PIP = pip3
    VENV = venv
    SEP = /
    RM = rm -rf
    SCRIPTS = bin
endif

# Main target
all: install

# Create a virtual environment
venv:
	$(PYTHON) -m $(VENV) venv

# Install project dependencies
install: venv
	.$(SEP)venv$(SEP)$(SCRIPTS)$(SEP)$(PIP) install -r requirements.txt
	.$(SEP)venv$(SEP)$(SCRIPTS)$(SEP)$(PIP) install -e ..$(SEP)prosody_guide$(SEP)misc$(SEP)

run:
	.$(SEP)venv$(SEP)$(SCRIPTS)$(SEP)$(PYTHON) src$(SEP)agent.py

# Clean up generated files and virtual environment
clean:
	$(RM) venv

# PHONY targets (targets that don't represent files)
.PHONY: all venv install clean