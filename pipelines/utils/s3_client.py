#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
S3 Client wrapper for data operations
"""

import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class S3Client:
    """Wrapper for AWS S3 operations"""
    
    def __init__(self, region_name: str = 'us-east-1'):
        self.s3_client = boto3.client('s3', region_name=region_name)
        self.region_name = region_name
    
    def list_objects(self, bucket: str, prefix: str = '') -> list:
        """List objects in S3 bucket"""
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix
            )
            return response.get('Contents', [])
        except ClientError as e:
            logger.error(f"Error listing objects: {e}")
            raise
    
    def upload_file(self, file_path: str, bucket: str, object_key: str):
        """Upload file to S3"""
        try:
            self.s3_client.upload_file(
                file_path,
                bucket,
                object_key
            )
            logger.info(f"Uploaded {file_path} to s3://{bucket}/{object_key}")
        except ClientError as e:
            logger.error(f"Error uploading file: {e}")
            raise
    
    def download_file(self, bucket: str, object_key: str, file_path: str):
        """Download file from S3"""
        try:
            self.s3_client.download_file(
                bucket,
                object_key,
                file_path
            )
            logger.info(f"Downloaded s3://{bucket}/{object_key} to {file_path}")
        except ClientError as e:
            logger.error(f"Error downloading file: {e}")
            raise
    
    def delete_object(self, bucket: str, object_key: str):
        """Delete object from S3"""
        try:
            self.s3_client.delete_object(Bucket=bucket, Key=object_key)
            logger.info(f"Deleted s3://{bucket}/{object_key}")
        except ClientError as e:
            logger.error(f"Error deleting object: {e}")
            raise
