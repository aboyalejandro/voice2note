import os
import boto3
from datetime import datetime
from utils import transcribe_audio

# AWS clients
s3_client = boto3.client("s3")
transcribe_client = boto3.client('transcribe')

# Lambda handler
def lambda_handler(event, context): 
    try:
        # Extract bucket and object info from event
        bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
        object_key = event["Records"][0]["s3"]["object"]["key"]
        
        print(f"New file detected: {object_key} in bucket {bucket_name}")

        # Download file from S3
        filename = os.path.basename(object_key)
        local_file_path = f"/tmp/{filename}"
        s3_client.download_file(bucket_name, object_key, local_file_path)
        print(f"File downloaded to {local_file_path}")

        # Transcribe audio
        transcript_text = transcribe_audio(bucket_name, object_key, transcribe_client)
    
    except Exception as e:
        print(f"Error in processing: {e}")
        raise