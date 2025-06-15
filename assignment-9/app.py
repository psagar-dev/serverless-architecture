import boto3
from datetime import datetime, timezone, timedelta
import os

BUCKET_NAME = os.environ.get('BUCKET_NAME', 'sagar-archive-demo-bucket')
AGE_DAYS = int(os.environ.get('AGE_DAY', 160)) # 6 months ≈ 180 days
GLACIER_CLASS = os.environ.get('GLACIER_CLASS', 'GLACIER')

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    now = datetime.now(timezone.utc)
    cutoff_date = now - timedelta(days=AGE_DAYS)
    archived = []

    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get('Contents', []):
            key = obj['Key']
            last_modified = obj['LastModified']
            storage_class = obj.get('StorageClass', 'STANDARD')

            # If object is older than cutoff and not already Glacier
            if last_modified < cutoff_date and storage_class not in ['GLACIER', 'DEEP_ARCHIVE']:
                s3.copy_object(
                    Bucket=BUCKET_NAME,
                    Key=key,
                    CopySource={'Bucket': BUCKET_NAME, 'Key': key},
                    StorageClass=GLACIER_CLASS,
                    MetadataDirective='COPY'
                )
                archived.append(key)

    return {'archived_files': archived}
