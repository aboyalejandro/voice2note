import boto3
import json
import os
from aws_lambda_powertools import Logger
from utils import (
    convert_to_webm,
    validate_file_extension,
    get_audio_metadata,
    save_to_postgresql,
    reencode_webm,
    save_metadata_to_s3,
)

# Setup logging
logger = Logger(service="v2n_audio_processing")

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

        logger.info(f"Processing file: {object_key} in bucket {bucket_name}")

        # Validate path
        if "audios/raw/" not in object_key:
            message = f"Skipping: {object_key} (not in audios/raw/)."
            logger.info(message)
            return {
                "statusCode": 200,
                "body": json.dumps({"message": message, "status": "skipped"}),
            }

        # Extract assets
        path_parts = object_key.split("/")
        user_id = path_parts[0].replace("user_", "")
        audio_key, extension = os.path.splitext(path_parts[3])

        # Validate file extension
        is_valid, media_format = validate_file_extension(object_key)
        if not is_valid:
            raise ValueError(
                f"Invalid file extension for {object_key}. Only .mp3, .wav, and .webm are supported."
            )

        # Download file from S3 to /tmp
        local_file_path = f"/tmp/{audio_key}.{media_format}"
        s3_client.download_file(bucket_name, object_key, local_file_path)

        # Re-encode if necessary
        reencoded_path = f"/tmp/reencoded_{os.path.basename(object_key)}"
        if media_format == "webm":
            reencode_webm(local_file_path, reencoded_path, FFMPEG_PATH)
            local_file_path = reencoded_path

        # Convert to WebM if necessary
        webm_file_path = f"/tmp/{audio_key}.webm"
        conversion_status = "no_conversion_needed"

        if media_format != "webm":
            convert_to_webm(local_file_path, webm_file_path, FFMPEG_PATH)
            logger.info(f"File converted from {media_format} to webm")
            conversion_status = "converted"
        else:
            logger.info(
                f"File is already in webm format, reencoding to ensure proper metadata"
            )
            reencode_webm(local_file_path, webm_file_path, FFMPEG_PATH)
            conversion_status = "reencoded"

        # Upload WebM file to S3
        compressed_key = f"user_{user_id}/audios/compressed/{audio_key}.webm"
        s3_client.upload_file(webm_file_path, bucket_name, compressed_key)
        logger.info(f"WebM file saved to S3 at {compressed_key}")

        # Get metadata object
        metadata = get_audio_metadata(local_file_path, FFMPEG_PATH)

        # Combine all metadata
        complete_metadata = {
            "format": media_format,
            **metadata,
            "s3_compressed_audio_url": f"s3://{bucket_name}/{compressed_key}",
            "conversion_status": conversion_status,
        }

        # Save complete metadata to PostgreSQL
        save_to_postgresql(
            user_id,
            audio_key,
            complete_metadata,
            DB_USER,
            DB_PASSWORD,
            DB_NAME,
            DB_HOST,
            DB_PORT,
        )

        # Save metadata JSON to S3
        metadata_s3_key = f"user_{user_id}/audios/metadata/{audio_key}.json"
        save_metadata_to_s3(
            s3_client,
            f"user_{user_id}",
            complete_metadata,
            bucket_name,
            metadata_s3_key,
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": f"Audio {object_key} processed successfully",
                    "status": "success",
                    "details": {
                        "user_id": user_id,
                        "audio_key": audio_key,
                        "original_path": object_key,
                        "compressed_path": compressed_key,
                        "metadata_path": metadata_s3_key,
                        "metadata": complete_metadata,
                    },
                }
            ),
        }

    except Exception as e:
        error_message = str(e)
        logger.error(f"Error processing file: {error_message}")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": "Error processing audio file",
                    "error": error_message,
                    "status": "error",
                }
            ),
        }
