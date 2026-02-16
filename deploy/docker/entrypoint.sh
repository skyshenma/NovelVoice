#!/bin/bash
set -e

# NovelVoice Docker Entrypoint Script

echo "🚀 Starting NovelVoice..."

# Create necessary directories
echo "📁 Creating data directories..."
mkdir -p /data/app /data/cache /data/config /data/db /data/logs

# Copy example config if config.yml doesn't exist
if [ ! -f "/data/config/config.yml" ]; then
    echo "⚠️  Config file not found, creating from example..."
    if [ -f "/app/data/config/config.example.yml" ]; then
        cp /app/data/config/config.example.yml /data/config/config.yml
        echo "✅ Config file created from example"
    else
        echo "⚠️  Example config not found, will use default config"
    fi
else
    echo "✅ Config file found"
fi

# Set permissions
chmod -R 755 /data

echo "✅ Initialization complete"

# Execute the main command
exec "$@"
