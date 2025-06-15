#https://chatgpt.com/c/684b8f16-73a0-8003-88bb-c81fa7419288
import boto3
import os
import json
import botocore

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def is_public_policy(policy):
    """Detect if a policy allows public access."""
    if not policy:
        return False
    for stmt in policy.get('Statement', []):
        effect = stmt.get('Effect', '')
        principal = stmt.get('Principal')
        if effect == 'Allow' and (principal == "*" or principal == {"AWS": "*"}) and \
           any(perm in stmt.get('Action', []) for perm in ["s3:GetObject", "s3:PutObject", "s3:*"]):
            return True
    return False

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    sns = boto3.client('sns')
    public_buckets = []

    # List all buckets
    # buckets = s3.list_buckets().get('Buckets', [])
    buckets = [{'Name': "sagar-s3-public-bucket"}]  # Example buckets for testing
    for bucket in buckets:
        bucket_name = bucket['Name']

        # 1. Check bucket ACL
        acl = s3.get_bucket_acl(Bucket=bucket_name)
        for grant in acl.get('Grants', []):
            grantee = grant.get('Grantee', {})
            if grantee.get('Type') == 'Group':
                uri = grantee.get('URI', '')
                # These are the URIs for "AllUsers" (public) and "AuthenticatedUsers"
                if 'AllUsers' in uri or 'AuthenticatedUsers' in uri:
                    permission = grant.get('Permission', '')
                    if permission in ['READ', 'WRITE', 'FULL_CONTROL']:
                        public_buckets.append(f"{bucket_name} (ACL: {permission})")

        # 2. Check bucket policy
        try:
            policy_str = s3.get_bucket_policy(Bucket=bucket_name)['Policy']
            policy = json.loads(policy_str)
            if is_public_policy(policy):
                public_buckets.append(f"{bucket_name} (Policy: Public Access)")
        except botocore.exceptions.ClientError as e:
            pass

    # Notify if public buckets found
    if public_buckets:
        message = "Public S3 Buckets detected:\n" + "\n".join(public_buckets)
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="Alert: Public S3 Bucket Detected",
            Message=message
        )
    else:
        print("No public buckets detected.")
    return {"public_buckets": public_buckets}
