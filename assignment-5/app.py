import boto3
import os
from datetime import datetime, timezone

def get_instance_ids(event):
    """
    Extract instance IDs from the EC2 launch event.
    """
    detail = event.get('detail', {})
    if 'instance-id' in detail:
        return [detail['instance-id']]
    elif 'instances' in detail:
        return [i['instance-id'] for i in detail['instances']]
    return []

def has_user_tag(ec2, instance_id):
    """
    Check if the instance already has the specified USER tag.
    """
    response = ec2.describe_instances(InstanceIds=[instance_id])
    tags = response['Reservations'][0]['Instances'][0].get('Tags', [])
    tag_key = os.environ.get('TAG_KEY', 'USER')
    tag_value = os.environ.get('TAG_VALUE', 'Sagar')

    for tag in tags:
        if tag['Key'] == tag_key and tag['Value'] == tag_value:
            return True
    return False

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    instance_ids = get_instance_ids(event)
    
    if not instance_ids:
        print("No instance IDs found.")
        return {
            "statusCode": 200,
            "body": {
                "status": "no-instances-found"
            }
        }

    print(f"Checking and tagging instances: {instance_ids}")
    tagged_instances = []
    skipped_instances = []

    for instance_id in instance_ids:
        if not has_user_tag(ec2, instance_id):
            print(f"[SKIP] Instance {instance_id} already has USER tag.")
            skipped_instances.append(instance_id)
            continue

        # Add tags
        tags = [
            {'Key': 'LaunchDate', 'Value': datetime.now(timezone.utc).strftime('%Y-%m-%d')},
            {'Key': 'Environment', 'Value': 'Development'}
        ]

        ec2.create_tags(Resources=[instance_id], Tags=tags)
        print(f"[TAGGED] Instance {instance_id} tagged.")
        tagged_instances.append(instance_id)

    return {
        "statusCode": 200,
        "body": {
            "status": "completed",
            "tagged": tagged_instances,
            "skipped": skipped_instances
        }
    }