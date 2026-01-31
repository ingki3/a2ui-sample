#!/bin/bash
source .venv/bin/activate
export PYTHONPATH=$(pwd)
python -m uvicorn app.api.main:app --host 0.0.0.0 --port 8000
