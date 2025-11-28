#!/bin/bash
set -e

MAX_RETRIES=5
RETRY_DELAY=10
REQUIREMENTS_FILE="$1"

if [ -z "$REQUIREMENTS_FILE" ]; then
    echo "Usage: $0 <requirements_file>"
    exit 1
fi

echo "Installing requirements from $REQUIREMENTS_FILE..."

for i in $(seq 1 $MAX_RETRIES); do
    echo "Attempt $i of $MAX_RETRIES..."
    
    if pip install --no-cache-dir --default-timeout=300 -r "$REQUIREMENTS_FILE"; then
        echo "Successfully installed requirements!"
        exit 0
    else
        if [ $i -lt $MAX_RETRIES ]; then
            echo "Installation failed. Retrying in ${RETRY_DELAY} seconds..."
            sleep $RETRY_DELAY
            RETRY_DELAY=$((RETRY_DELAY * 2))  # Exponential backoff
        else
            echo "Failed to install requirements after $MAX_RETRIES attempts."
            exit 1
        fi
    fi
done

