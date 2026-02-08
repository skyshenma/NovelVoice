#!/bin/bash
set -e

# NovelVoice Docker Entrypoint Script

echo "🚀 Starting NovelVoice..."

# Check if config file exists, if not copy from example
if [ ! -f "/data/config/config.yml" ]; then
    echo "📝 Config file not found, creating from example..."
    cp /app/data/config/config.example.yml /data/config/config.yml
    echo "✅ Config file created at /data/config/config.yml"
fi

# Create necessary directories
mkdir -p /data/app /data/cache

# Set permissions
chmod -R 755 /data

echo "✅ Initialization complete"

# Execute the main command
exec "$@"
