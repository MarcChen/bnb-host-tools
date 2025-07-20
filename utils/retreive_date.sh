#!/bin/bash

# Variabilize the project directory
PROJECT_DIR="/home/marc/bnb-host-tools"

# Change to the project directory
cd "$PROJECT_DIR" || exit 1

# Source bashrc to load environment variables and functions
source ~/.bashrc

# Set environment variables (assuming set_env_vars is a function or script)
set_env_vars

# Run the Python script using poetry
poetry run python services/dataviz/src/get_blocked_days.py

# To set up a cron job to run this script, use the following command:
# (This example runs the script every day at 2:00 AM)
# Edit your crontab with: crontab -e
# Add the following line:
# 0 2 * * * /home/marc/projets/bnb-host-tools/utils/retreive_date.sh >> /home/marc/projets/bnb-host-tools/utils/retreive_date.log 2>&1