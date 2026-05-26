#!/bin/bash

set -e

echo "Starting Financial Risk Lakehouse platform..."

# Load environment
source /opt/airflow/.env

# Initialize Airflow database
echo "Initializing Airflow database..."
airflow db init

# Create default user if needed
echo "Creating Airflow admin user..."
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin123 || echo "Admin user already exists"

# Start Airflow scheduler and webserver
echo "Starting Airflow services..."
exec docker-compose up -d

echo "Platform startup complete!"
