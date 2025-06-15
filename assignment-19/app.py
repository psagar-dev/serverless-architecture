import boto3
import os

TARGET_GROUP_ARN = os.environ.get("TARGET_GROUP_ARN")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

elbv2 = boto3.client('elbv2')
sns = boto3.client('sns')

def lambda_handler(event, context):
    try:
        response = elbv2.describe_target_health(TargetGroupArn=TARGET_GROUP_ARN)
        target_health_descriptions = response['TargetHealthDescriptions']

        unhealthy_targets = [
            t for t in target_health_descriptions 
            if t['TargetHealth']['State'] != 'healthy'
        ]

        if unhealthy_targets:
            msg_lines = [
                f"Unhealthy targets detected in Target Group:",
                f"Target Group ARN: {TARGET_GROUP_ARN}",
                ""
            ]
            for t in unhealthy_targets:
                target = t['Target']
                health = t['TargetHealth']
                msg_lines.append(
                    f"Target ID: {target['Id']}, Port: {target['Port']}, "
                    f"State: {health['State']}, Reason: {health.get('Reason','')}, "
                    f"Description: {health.get('Description','')}"
                )
            message = "\n".join(msg_lines)

            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="ALERT: Unhealthy targets in ALB Target Group",
                Message=message
            )
        else:
            print("All targets are healthy.")

    except Exception as e:
        print(f"Error: {e}")
