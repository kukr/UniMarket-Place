import boto3
import json
import os

# authenticate with AWS from .env file
ACCESS_KEY = os.getenv('AWS_ACCESS_KEY')
SECRET_KEY = os.getenv('AWS_SECRET_KEY')


s3 = boto3.client('s3', aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY)
s3_bucket_name = '409images'
