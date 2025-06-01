import boto3
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """
    AWS Lambda function to detect S3 buckets without default server-side encryption.
    Returns a list of unencrypted bucket names.
    """
    s3 = boto3.client('s3')
    unencrypted_buckets = []

    # List all buckets in the account
    try:
        response = s3.list_buckets()
        buckets_to_check = response.get('Buckets', [])
    except ClientError as e:
        print(f"❌ Error listing buckets: {e}")
        return {"unencrypted_buckets": []}

    for bucket in buckets_to_check:
        bucket_name = bucket['Name']
        try:
            s3.get_bucket_encryption(Bucket=bucket_name)
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ServerSideEncryptionConfigurationNotFoundError':
                unencrypted_buckets.append(bucket_name)
            else:
                print(f"⚠️  Error checking {bucket_name}: {e}")

    if unencrypted_buckets:
        print("\n🔒 Unencrypted Buckets Detected:")
        for b in unencrypted_buckets:
            print(f"❌ {b}")
    else:
        print("\n✅ All buckets have server-side encryption enabled.")

        # Return for integration/automation
        return {"unencrypted_buckets": unencrypted_buckets}
