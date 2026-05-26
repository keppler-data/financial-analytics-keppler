#!/bin/bash
# Cleanup script

set -e

ENVIRONMENT=${1:-dev}

echo "=== Cleanup Script for $ENVIRONMENT Environment ==="
echo ""
echo "⚠️  This will clean local data and containers"
echo ""
read -p "Are you sure? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Cleanup cancelled"
    exit 0
fi

# Source environment
source master/profiles/${ENVIRONMENT}.env

# Remove data directories
if [ "$ENVIRONMENT" = "dev" ]; then
    echo "Removing local data directories..."
    rm -rf data/raw data/bronze data/silver data/intermediate data/gold data/diamond
    mkdir -p data/{raw,bronze,silver,intermediate,gold,diamond}
fi

# Remove Docker containers and volumes
echo "Stopping Docker services..."
docker-compose -f master/docker-compose.yml down -v

# Remove logs
echo "Cleaning logs..."
rm -rf airflow/logs/*
rm -rf *.log

echo "Cleanup complete!"
