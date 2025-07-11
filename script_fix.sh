#!/bin/bash

# 🧼 Clean everything
rm -rf .venv uv.env uv.cache poetry.lock

# 🧪 Recreate virtual env with Python 3.11
/opt/homebrew/opt/python@3.11/bin/python3.11 -m venv .venv
source .venv/bin/activate

# 📦 Upgrade pip
pip install --upgrade pip

# 📄 Reinstall dependencies
pip install -r requirements.txt

# 🚀 Run the server
uvicorn main:app --reload
