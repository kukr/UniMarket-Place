import boto3
import json

# authenticate with AWS from json file
with open('aws_config.json') as f:
    data = json.load(f)
    ACCESS_KEY = data['access_key']
    SECRET_KEY = data['secret']

s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY)
s3_bucket_name = '409images'
