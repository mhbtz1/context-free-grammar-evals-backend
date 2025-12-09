#!/bin/bash

NAME="cfg-server"
NUM_WORKERS=${GUNICORN_WORKERS:-20}
NUM_THREADS=${GUNICRON_THREADS:-20}
HOST="$1"
PORT="$2"

MAX_REQUESTS=${GUNICORN_MAX_REQUESTS:-1000}
MAX_REQUESTS_JITTER=${GUNICORN_MAX_REQUESTS_JITTER:-3000}
FASTAPI_APP="server:app"

init_fastapi_server() {
    if [ -f "/opt/venv/bin/gunicorn" ]; then
        GUNICORN_BIN="/opt/venv/bin/gunicorn"
    elif [ -f "$HOME/.virtualenvs/.cfg-eval/bin/gunicorn" ]; then
        GUNICORN_BIN="$HOME/.virtualenvs/.cfg-eval/bin/gunicorn"
    else
        GUNICORN_BIN="gunicorn"
    fi
    
    PYTHONPATH=. $GUNICORN_BIN $FASTAPI_APP \
        --bind ${HOST}:${PORT} \
        --name $NAME \
        --workers $NUM_WORKERS \
        --threads $NUM_THREADS \
        --timeout 600 \
        --max-requests $MAX_REQUESTS \
        --max-requests-jitter $MAX_REQUESTS_JITTER \
        --worker-class uvicorn.workers.UvicornWorker 2>&1
}

init_fastapi_server