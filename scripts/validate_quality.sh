#!/bin/bash
# Validate data quality script

set -e

ENVIRONMENT=${1:-dev}
LOG_FILE="validation_${ENVIRONMENT}_$(date +%Y%m%d_%H%M%S).log"

echo "Starting data quality validation for $ENVIRONMENT environment..." | tee $LOG_FILE

# Source environment
source master/profiles/${ENVIRONMENT}.env

# Run quality checks
echo "Running quality checks..." | tee -a $LOG_FILE

# Check Bronze layer
echo "Checking Bronze layer..." | tee -a $LOG_FILE
if [ -d "$BRONZE_PATH" ]; then
    BRONZE_FILES=$(find $BRONZE_PATH -type f | wc -l)
    echo "Bronze files count: $BRONZE_FILES" | tee -a $LOG_FILE
fi

# Check Silver layer
echo "Checking Silver layer..." | tee -a $LOG_FILE
if [ -d "$SILVER_PATH" ]; then
    SILVER_FILES=$(find $SILVER_PATH -type f | wc -l)
    echo "Silver files count: $SILVER_FILES" | tee -a $LOG_FILE
fi

# Check Intermediate layer
echo "Checking Intermediate layer..." | tee -a $LOG_FILE
if [ -d "$INTERMEDIATE_PATH" ]; then
    INT_FILES=$(find $INTERMEDIATE_PATH -type f | wc -l)
    echo "Intermediate files count: $INT_FILES" | tee -a $LOG_FILE
fi

# Check Gold layer
echo "Checking Gold layer..." | tee -a $LOG_FILE
if [ -d "$GOLD_PATH" ]; then
    GOLD_FILES=$(find $GOLD_PATH -type f | wc -l)
    echo "Gold files count: $GOLD_FILES" | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE
echo "Validation complete. Log saved to: $LOG_FILE" | tee -a $LOG_FILE
