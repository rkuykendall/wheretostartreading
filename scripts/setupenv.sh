#!/bin/bash
# Create a Python virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
export CFLAGS="-I$(brew --prefix)/include"
export LDFLAGS="-L$(brew --prefix)/lib"
pip install -r requirements.txt
