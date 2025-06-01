import boto3

def lambda_handler(event, context):
    # Create an EC2 client
    ec2 = boto3.client('ec2')

    # Find instances with tag Action=Auto-Stop
    stop_response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Action', 'Values': ['Auto-Stop']},
            {'Name': 'tag:USER', 'Values': ['Sagar']},
            {'Name': 'instance-state-name', 'Values': ['running']}
        ]
    )

    instances_to_stop = [
        instance['InstanceId']
        for reservation in stop_response['Reservations']
        for instance in reservation['Instances']
    ]

    # Find instances with tag Action=Auto-Start
    start_response = ec2.describe_instances(
        Filters=[
            {'Name': 'tag:Action', 'Values': ['Auto-Start']},
            {'Name': 'tag:USER', 'Values': ['Sagar']},
            {'Name': 'instance-state-name', 'Values': ['stopped']}
        ]
    )

    instances_to_start = [
        instance['InstanceId']
        for reservation in start_response['Reservations']
        for instance in reservation['Instances']
    ]

    # Stop instances
    if instances_to_stop:
        print(f"Stopping: {instances_to_stop}")
        ec2.stop_instances(InstanceIds=instances_to_stop)
    else:
        print("No instances to stop.")

    # Start instances
    if instances_to_start:
        print(f"Starting: {instances_to_start}")
        ec2.start_instances(InstanceIds=instances_to_start)
    else:
        print("No instances to start.")

    # Print the results
    return {
        'StoppedInstances': instances_to_stop,
        'StartedInstances': instances_to_start
    }
