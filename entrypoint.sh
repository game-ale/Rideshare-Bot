#!/bin/bash
set -e

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the FastAPI server in the background
echo "Starting FastAPI Admin Server..."
uvicorn api.main:app --host 0.0.0.0 --port 8001 &
API_PID=$!

# Start the Telegram Bot in the foreground
echo "Starting Telegram Bot..."
python app.py &
BOT_PID=$!

# Wait for any process to exit
wait -n

# Exit with the status of the first process to exit
exit $?
