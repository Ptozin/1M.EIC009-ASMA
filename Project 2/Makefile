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
	uv pip install -r requirements.txt

run:
	.$(SEP).venv$(SEP)$(SCRIPTS)$(SEP)$(PYTHON) src$(SEP)main.py

# To train the models, run the following command
train:
	.$(SEP).venv$(SEP)$(SCRIPTS)$(SEP)$(PYTHON) src$(SEP)train.py

# To test the models, run the following command, reminder: change manually the model path, according to tensorboard logs!
test:
	.$(SEP).venv$(SEP)$(SCRIPTS)$(SEP)$(PYTHON) src$(SEP)load.py

tensorboard:
	tensorboard --logdir=logs

# clean up generated files and virtual environment

clean:
	$(RM) .venv
	$(RM) src$(SEP)__pycache__
	$(RM) src$(SEP)models$(SEP)__pycache__
	$(RM) src$(SEP)environments$(SEP)__pycache__
	$(RM) __pycache__

# PHONY targets (targets that don't represent files)
.PHONY: all venv install clean