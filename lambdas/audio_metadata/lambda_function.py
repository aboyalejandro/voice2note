import os
import boto3
import json
from aws_lambda_powertools import Logger
from utils import get_audio_metadata, save_metadata_to_postgresql

# Setup logging
logger = Logger(service="v2n_audio_metadata_processing")

# AWS clients
s3_client = boto3.client("s3")

# PostgreSQL connection parameters from environment variables
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

# Path to ffmpeg binary from the layer
FFMPEG_PATH = "/opt/bin/ffmpeg"


def lambda_handler(event, context):
    try:
        # Extract bucket and object info from SNS event
        message = event["Records"][0]["Sns"]["Message"]
        message = json.loads(message)
        bucket_name = message["bucket_name"]
        object_key = message["object_key"]

        logger.info(f"New file detected: {object_key} in bucket {bucket_name}")

        # Validate path
        if "audios/raw/" not in object_key:
            logger.info(f"Skipping: {object_key} (not in audios/raw/).")
            return

        # Validate path structure
        path_parts = object_key.split("/")
        if (
            len(path_parts) != 4
            or not path_parts[0].startswith("user_")
            or path_parts[1] != "audios"
            or path_parts[2] != "raw"
        ):
            raise ValueError(
                "Invalid path structure. Expected: user_{user_id}/audios/raw/filename.wav"
            )

        user_id = path_parts[0].replace("user_", "")
        audio_key = path_parts[3].replace(".wav", "")

        # Download file from S3 to /tmp
        local_file_path = f"/tmp/{audio_key}.wav"
        s3_client.download_file(bucket_name, object_key, local_file_path)

        # Extract metadata
        metadata = get_audio_metadata(local_file_path, FFMPEG_PATH)

        # Save metadata to S3
        metadata_key = f"user_{user_id}/audios/metadata/{audio_key}.json"
        s3_client.put_object(
            Bucket=bucket_name,
            Key=metadata_key,
            Body=json.dumps(metadata),
            ContentType="application/json",
        )
        logger.info(f"Metadata saved to S3 at {metadata_key}")

        # Update PostgreSQL
        save_metadata_to_postgresql(
            user_id,
            audio_key,
            metadata,
            DB_USER,
            DB_PASSWORD,
            DB_NAME,
            DB_HOST,
            DB_PORT,
        )

        return {
            "statusCode": 200,
            "body": f"Metadata processed and saved for {object_key}.",
        }

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise