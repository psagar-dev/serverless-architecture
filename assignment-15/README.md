### 🚀 **Assignment 15: Implement a Log Cleaner for S3**

#### 🗂️ **Step 1: Setting Up Your S3 Bucket**

#### 🪣 **1.1 Create Your Bucket**

1. Log into the [AWS S3 Console](https://console.aws.amazon.com/s3/).
2. Click **Create bucket**.
3. Provide a globally unique bucket name (e.g., `s3-bucket-log-cleaner`).
4. Choose your preferred region.
5. Click **Create bucket**.

#### 📤 **1.2 Uploading Files**

1. Select your bucket.
2. Click **Upload** and add files (log file, etc.).
3. Complete the upload.

#### **🔐 Step 2: Create Lambda IAM Role**

##### 🔑 **2.1 Create an IAM Role**

1. Navigate to the [AWS IAM Console](https://console.aws.amazon.com/iam/).
2. Click **Roles > Create role**.
3. Select **AWS service** and choose **Lambda**.
4. Click **Next**.
![Step One for role](../assignment-1/images/role-1.png)
#### 🛡️ **2.2 Attach Permissions**

1. Search and select `AmazonS3FullAccess` (for simplicity).
2. Click **Next**.
![Add Permission](../assignment-9/images/iam-permission.png)
#### 📝 **2.3 Finalize Role Creation**

1. Name the role, e.g., `sagar-s3-log-cleaner-role`.
2. Click **Create role**.
![Create Role](images/create-role.png)

#### ⚡ **Step 3: Create Lambda Function**

##### 3.1 🏃‍♂️ Go to Lambda Console

1. In AWS Console, 🔎 search for and select **Lambda**.
2. Click **Create function**

##### 3.2 ⚙️ Configure Function

1. **Author from scratch**

   * 📝 Name: `s3-log-cleaner`
   * 🐍 Runtime: **Python 3.12**
2. **Change default execution role:**

   * Select **Use an existing role**
   * Choose the `sagar-s3-log-cleaner-role` you just created
3. ✅ Click **Create function**
![Create Lambda function](images/create-lambda-function.png)

##### 3.3 Lambda Python Script

For best practice, set this as an **environment variable** in the Lambda console.

```python
import boto3
from datetime import datetime, timezone, timedelta
import os

# You can use environment variables for these
BUCKET_NAME = os.environ.get('BUCKET_NAME','sagar-s3-logs-bucket')
LOG_PREFIX = os.environ.get('LOG_PREFIX', 'logs/') 
DAYS_THRESHOLD = int(os.environ.get('DAYS_THRESHOLD', 90))

def lambda_handler(event, context):
    s3 = boto3.client('s3')
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=DAYS_THRESHOLD)
    deleted_files = []

    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=BUCKET_NAME, Prefix=LOG_PREFIX):
        for obj in page.get('Contents', []):
            key = obj['Key']
            last_modified = obj['LastModified']

            if last_modified < cutoff:
                s3.delete_object(Bucket=BUCKET_NAME, Key=key)
                deleted_files.append(key)
                print(f"Deleted {key} last modified at {last_modified}")
                
    return {
        'statusCode': 200,
        'body': f"Deleted {len(deleted_files)} log files."
    }
```

Click **Deploy**.

##### 🛠️ **3.4 Configure Environment Variables**

1. Click on the **Configuration** tab in Lambda.
2. Go to **Environment variables** and add:

   * `BUCKET_NAME`: e.g., `sagar-s3-logs-bucket`
   * `LOG_PREFIX`: e.g., `logs/`
   * `DAYS_THRESHOLD`: e.g., `90`

Click **Save**.

#### **⏰ Step 4 Schedule Lambda with CloudWatch Events**

1. Go to your Lambda function.
2. Click **Add trigger** > **EventBridge (CloudWatch Events)**.
3. Name: `weekly-s3-log-cleaner`
4. Set the schedule expression (e.g., `cron(0 2 ? * MON *)`) (Runs every Monday at **2 AM UTC**; change as needed).
5. Click **Add**.
![CloudWatch Events](images/cloudWatch-events.png)

#### **🧪 Step 5: Manual Test & Validation**
##### 5.1 🧑‍🔬 Test in Lambda Console

1. In your Lambda function page, click **Test**.
2. For the first time, it asks to "Configure test event":

   * 📝 **Event name:** (`test-s3-log-cleaner`)
   - Leave the event JSON as `{}` (empty event)
   * Click **Save**
3. 🟢 Click **Test** (again) to **run** the function.
![Test Function](images/test-function.png)

##### 5.2 Automation
- Automatically Delete log file.

##### 5.3 🔍 Validation
- You go to bucket then check it