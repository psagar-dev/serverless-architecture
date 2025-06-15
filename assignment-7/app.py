import boto3
import os
import json

SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
sns = boto3.client('sns')

def lambda_handler(event, context):
    for record in event.get('Records', []):
        if record['eventName'] == 'MODIFY':
            old_image = record['dynamodb'].get('OldImage', {})
            new_image = record['dynamodb'].get('NewImage', {})
            
            # Convert DynamoDB types to JSON
            def ddb_to_dict(image):
                return {k: list(v.values())[0] for k, v in image.items()}
            
            old = ddb_to_dict(old_image)
            new = ddb_to_dict(new_image)

            message = (
                f"DynamoDB item updated:\n\n"
                f"Old values: {json.dumps(old, indent=2)}\n\n"
                f"New values: {json.dumps(new, indent=2)}"
            )

            # Publish to SNS
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="DynamoDB Item Updated",
                Message=message
            )

            print(f"Alert sent:\n{message}")
    return {"status": "done"}