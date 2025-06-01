import boto3
from datetime import datetime, timezone, timedelta
import os

BUCKET_NAME = os.environ.get('BUCKET_NAME', 'sagar-s3-cleanup-bucket')
DAYS_TO_KEEP = int(os.environ.get('DAYS_TO_KEEP', 30))

s3 = boto3.client('s3')

def lambda_handler(event, context):
    """
        Lambda function to delete files older than DAYS_TO_KEEP days from the S3 bucket.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=DAYS_TO_KEEP)
    deleted_files = []
    errors = []

    paginator = s3.get_paginator('list_objects_v2')

    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get('Contents', []):
            key = obj['Key']
            last_modified = obj['LastModified']
            if last_modified < cutoff:
                try:
                    # Attempt to delete the object
                    s3.delete_object(Bucket=BUCKET_NAME, Key=key)
                    deleted_files.append(key)
                except Exception as e:
                    # Collect error info for result/reporting
                    errors.append({'key': key, 'error': str(e)})
    return {
        'statusCode': 200 if not errors else 207,
        'body': {
            'deleted_files': deleted_files,
            'deleted_count': len(deleted_files),
            'errors': errors
        }
    }