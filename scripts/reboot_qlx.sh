#!/bin/bash

echo "--- QUARLEX MAINTENANCE INITIATED ---"

# 1. Force kill anything on Port 80
echo "Clearing Port 80..."
fuser -k 80/tcp

# 2. Kill all existing python3 instances (optional but safer)
echo "Stopping all Python instances..."
pkill -f python3

# 3. Wait 1 second for the port to breathe
sleep 1

# 4. Launch the core in the background
echo "Launching QLX Core v5.7..."
nohup python3 qlx_core.py > qlx.log 2>&1 &

echo "SUCCESS: Server is running in the background."
echo "Check qlx.log if it fails."
