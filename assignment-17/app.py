import boto3
import os

# CONFIGURATION
INSTANCE_TYPE = os.environ.get('INSTANCE_TYPE','t2.micro')
KEY_NAME = os.environ.get('KEY_NAME', 'sagar-key')
SECURITY_GROUP_IDS_VALUE = os.environ.get('SECURITY_GROUP_IDS_VALUE')
SECURITY_GROUP_IDS = SECURITY_GROUP_IDS_VALUE.split(',') if SECURITY_GROUP_IDS_VALUE else []
SUBNET_ID = os.environ.get('SUBNET_ID','subnet-xxxxxxxx')
VOLUME_TAG_KEY = os.environ.get('VOLUME_TAG_KEY','Backup')
VOLUME_TAG_VALUE = os.environ.get('VOLUME_TAG_VALUE','True')
AVAILABILITY_ZONE = os.environ.get('AVAILABILITY_ZONE','ap-south-1a')
IMAGE_ID = os.environ.get('IMAGE_ID', 'ami-0fc5d935ebf8bc3bc')  # Dummy AMI for networking

ec2 = boto3.client('ec2')

def lambda_handler(event, context):
    # Step 1: Find the latest snapshot with specific tags
    snapshots = ec2.describe_snapshots(
        Filters=[
            {'Name': 'tag:' + VOLUME_TAG_KEY, 'Values': [VOLUME_TAG_VALUE]},
            {'Name': 'tag:USER', 'Values': ['Sagar']}
        ],
        OwnerIds=['self']
    )['Snapshots']
    
    if not snapshots:
        raise Exception("No snapshots found with the given tag")

    latest_snapshot = max(snapshots, key=lambda x: x['StartTime'])
    print(f"Latest snapshot found: {latest_snapshot}")
    # Step 2: Create a volume from the latest snapshot
    volume_response = ec2.create_volume(
        SnapshotId=latest_snapshot['SnapshotId'],
        AvailabilityZone=AVAILABILITY_ZONE,
        VolumeType='gp3',
        TagSpecifications=[
            {
                'ResourceType': 'volume',
                'Tags': [{'Key': 'RestoredFrom', 'Value': latest_snapshot['SnapshotId']}]
            }
        ]
    )
    volume_id = volume_response['VolumeId']
    print(f"Created volume {volume_id} from snapshot")

    # Wait for volume to become available
    waiter = ec2.get_waiter('volume_available')
    waiter.wait(VolumeIds=[volume_id])

    # Step 3: Launch a new EC2 instance with this volume as the root
    instance_response = ec2.run_instances(
        ImageId=IMAGE_ID,  # Use a dummy AMI for networking; will detach its root.
        InstanceType=INSTANCE_TYPE,
        KeyName=KEY_NAME,
        MaxCount=1,
        MinCount=1,
        NetworkInterfaces=[
            {
                'DeviceIndex': 0,
                'SubnetId': SUBNET_ID,
                'Groups': SECURITY_GROUP_IDS,
                'AssociatePublicIpAddress': True
            }
        ],
        BlockDeviceMappings=[
            {
                'DeviceName': '/dev/xvda',
                'Ebs': {
                    'VolumeSize': latest_snapshot['VolumeSize'],
                    'VolumeType': 'gp3',
                    'DeleteOnTermination': True,
                    'SnapshotId': latest_snapshot['SnapshotId']
                }
            }
        ],
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': 'RestoredFromSnapshot'},{'Key': 'USER', 'Value': 'Sagar'}]
            }
        ]
    )

    instance_id = instance_response['Instances'][0]['InstanceId']
    print(f"Launched EC2 instance {instance_id} from snapshot")

    return {
        'status': 'Success',
        'instance_id': instance_id,
        'snapshot_id': latest_snapshot['SnapshotId'],
        'volume_id': volume_id
    }
