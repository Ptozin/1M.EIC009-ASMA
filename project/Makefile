# detect OS
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

# main target
all: install

# create a virtual environment
venv:
	uv venv
	.venv$(SEP)$(SCRIPTS)$(SEP)activate

# install project dependencies using uv
install: venv
	uv $(PIP) install -r requirements.txt

run:
	.$(SEP).venv$(SEP)$(SCRIPTS)$(SEP)$(PYTHON) src$(SEP)main.py

# clean up generated files and virtual environment

clean:
	$(RM) .venv
	$(RM) src$(SEP)__pycache__
	$(RM) __pycache__

# PHONY targets (targets that don't represent files)
.PHONY: all venv install clean