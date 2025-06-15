import boto3
import os
from datetime import datetime, timedelta

# Set your billing threshold and SNS topic ARN
BILLING_THRESHOLD = float(os.environ.get("BILLING_THRESHOLD", "50.0"))
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN")

cloudwatch = boto3.client('cloudwatch', region_name='ap-south-1')
sns = boto3.client('sns')

def lambda_handler(event, context):
    try:
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/Billing',
            MetricName='EstimatedCharges',
            Dimensions=[{'Name': 'Currency', 'Value': 'USD'}],
            StartTime=datetime.utcnow() - timedelta(days=1),
            EndTime=datetime.utcnow(),
            Period=86400,
            Statistics=['Maximum']
        )

        datapoints = response['Datapoints']
        if not datapoints:
            print("No billing data available yet.")
            return

        latest_point = sorted(datapoints, key=lambda x: x['Timestamp'])[-1]
        cost = latest_point['Maximum']

        print(f"Current estimated charges: ${cost:.2f}")

        if cost > BILLING_THRESHOLD:
            message = f"⚠️ AWS Billing Alert:\nYour estimated charges are ${cost:.2f}, which exceeds your threshold of ${BILLING_THRESHOLD:.2f}."
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject="🚨 AWS Billing Alert",
                Message=message
            )
            print("SNS alert sent.")
            return {"status": "alert_sent", "cost": cost}
        else:
            print("Billing is within the threshold.")
            return {"status": "within_threshold", "cost": cost}

    except Exception as e:
        print(f"Error: {str(e)}")
        return {"status": "error", "message": str(e)}
