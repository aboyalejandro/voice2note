import boto3
import json
import os
from aws_lambda_powertools import Logger
from utils import convert_to_webm, validate_file_extension, update_metadata

# Setup logging
logger = Logger(service="v2n_audio_compression")

# AWS clients
s3_client = boto3.client("s3")
aws_region = "eu-east-1"

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

        # Extract assets
        path_parts = object_key.split("/")
        user_id = path_parts[0].replace("user_", "")
        audio_key, extension = os.path.splitext(path_parts[3])

        # Validate file extension
        if not validate_file_extension(object_key):
            raise ValueError(
                f"Invalid file extension for {object_key}. Only .mp3, .wav, and .webm are supported."
            )

        # Download file from S3 to /tmp
        local_file_path = f"/tmp/{audio_key}{extension}"
        s3_client.download_file(bucket_name, object_key, local_file_path)

        # Convert to WebM if necessary
        if extension.lower() != ".webm":
            webm_file_path = f"/tmp/{audio_key}.webm"
            convert_to_webm(local_file_path, webm_file_path, FFMPEG_PATH)
        else:
            logger.info(
                f"File extension is already {extension.lower()}, no need for conversion."
            )
            webm_file_path = local_file_path  # No conversion needed

        # Upload converted Webm file to S3
        compressed_key = f"user_{user_id}/audios/compressed/{audio_key}.webm"
        s3_client.upload_file(webm_file_path, bucket_name, compressed_key)
        logger.info(f"SavedWebM file saved to S3 at {compressed_key}")
        compressed_audio_url = f"s3://{bucket_name}/{compressed_key}"

        # Update metadata with compressed audio URL path
        update_metadata(
            user_id,
            audio_key,
            {"s3_compressed_audio_url": compressed_audio_url},
            DB_USER,
            DB_PASSWORD,
            DB_NAME,
            DB_HOST,
            DB_PORT,
        )

        return {"statusCode": 200, "body": f"Audio {object_key} converted to WebM"}

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise
