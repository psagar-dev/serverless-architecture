import boto3
import os
from datetime import datetime, timedelta, timezone

# ENV VARS
ELB_NAME = os.environ['ELB_NAME']           # e.g., 'app/my-app/0123456789abcdef'
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']
THRESHOLD = int(os.environ.get('THRESHOLD', 10))

cloudwatch = boto3.client('cloudwatch')
sns = boto3.client('sns')

def lambda_handler(event, context):
    # Time window: last 5 minutes
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=5)

    # Query ELB 5XX count (ELB or ALB: adjust accordingly)
    metric_dimensions = [
        {'Name': 'LoadBalancer', 'Value': ELB_NAME}
    ]

    # For ALB: Use 'HTTPCode_Target_5XX_Count'
    response = cloudwatch.get_metric_statistics(
        Namespace='AWS/ApplicationELB',
        MetricName='HTTPCode_Target_5XX_Count',
        Dimensions=metric_dimensions,
        StartTime=start_time,
        EndTime=end_time,
        Period=300,
        Statistics=['Sum'],
    )

    datapoints = response['Datapoints']
    error_count = int(datapoints[0]['Sum']) if datapoints else 0

    print(f"[INFO] ELB 5xx errors in last 5 minutes: {error_count}")

    if error_count > THRESHOLD:
        message = (
            f"ALERT: {error_count} 5xx errors detected on ELB '{ELB_NAME}' in the last 5 minutes.\n"
            f"Threshold: {THRESHOLD}\n"
            f"Time window: {start_time.strftime('%Y-%m-%d %H:%M:%S')} to {end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="ALERT: ELB 5xx Errors Spiked",
            Message=message,
        )
        print("[INFO] SNS notification sent.")
    else:
        print("[INFO] No alert triggered.")

    return {
        "statusCode": 200,
        "body": f"Checked {ELB_NAME}: {error_count} 5xx errors in last 5 min."
    }