import boto3
from datetime import datetime, timezone, timedelta
import os

# You can use environment variables for these
BUCKET_NAME = os.environ.get('BUCKET_NAME','sagar-s3-logs-bucket')
LOG_PREFIX = os.environ.get('LOG_PREFIX', 'logs/') 
DAYS_THRESHOLD = int(os.environ.get('DAYS_THRESHOLD', 90))

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=DAYS_THRESHOLD)
    deleted_files = []

    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=LOG_PREFIX):
        for obj in page.get('Contents', []):
            key = obj['Key']
            last_modified = obj['LastModified']

            if last_modified < cutoff:
                s3.delete_object(Bucket=BUCKET_NAME, Key=key)
                deleted_files.append(key)
                print(f"Deleted {key} last modified at {last_modified}")
                
    return {
        'statusCode': 200,
        'body': f"Deleted {len(deleted_files)} log files."
    }