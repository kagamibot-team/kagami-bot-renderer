#!/bin/bash

cd /opt/kagami-renderer/
source ./.venv/bin/activate
git pull
pip install -r requirements.txt
python main.py
