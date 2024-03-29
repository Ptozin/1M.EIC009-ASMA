# Detect OS
ifeq ($(OS),Windows_NT)
    # Windows settings
    PYTHON = python
    PIP = pip
    SEP = \\
    RM = - rd /s /q
    SCRIPTS = Scripts
else
    # Unix/Linux settings
    PYTHON = python3
    PIP = pip3
    SEP = /
    RM = rm -rf
    SCRIPTS = bin
endif

# Main target
all: install

# Create a virtual environment
venv:
	uv venv
	.venv$(SEP)$(SCRIPTS)$(SEP)activate

# Install project dependencies using uv
install: venv
	uv $(PIP) install -r requirements.txt
	uv $(PIP) install -e ..$(SEP)'theorical practices'$(SEP)prosody_guide$(SEP)misc$(SEP)

run:
	.$(SEP).venv$(SEP)$(SCRIPTS)$(SEP)$(PYTHON) src$(SEP)__main__.py

visualization:
	.$(SEP).venv$(SEP)$(SCRIPTS)$(SEP)$(PYTHON) src$(SEP)visualization.py

# Clean up generated files and virtual environment

clean:
	$(RM) .venv
	$(RM) src$(SEP)__pycache__
	$(RM) __pycache__

# PHONY targets (targets that don't represent files)
.PHONY: all venv install clean