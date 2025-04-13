#!/bin/bash

# Change to project directory
cd "$(dirname "$0")/.."

# Activate virtual environment
source venv/bin/activate

# Run Django management command
python manage.py update_orders

# Deactivate virtual environment
deactivate
