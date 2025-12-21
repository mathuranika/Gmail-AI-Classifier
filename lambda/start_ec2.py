import boto3
import os
from dotenv import load_dotenv

load_dotenv()
EC2_INSTANCE_ID = os.getenv("EC2_INSTANCE_ID")
def lambda_handler(event, context):
    ec2 = boto3.client("ec2")
    ec2.start_instances(InstanceIds=[EC2_INSTANCE_ID])

    return {
        "statusCode": 200,
        "body": "EC2 started successfully"
    }
