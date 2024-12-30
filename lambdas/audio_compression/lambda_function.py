import boto3
import json
from aws_lambda_powertools import Logger
from utils import convert_to_amr

# Setup logging
logger = Logger(service="v2n_audio_compression")

# AWS clients
s3_client = boto3.client("s3")

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

        # Convert to AMR
        amr_file_path = f"/tmp/{audio_key}.amr"
        convert_to_amr(local_file_path, amr_file_path, FFMPEG_PATH)

        # Upload converted AMR file to S3
        compressed_key = f"user_{user_id}/audios/compressed/{audio_key}.amr"
        s3_client.upload_file(amr_file_path, bucket_name, compressed_key)
        logger.info(f"Converted AMR file saved to S3 at {compressed_key}")

        return {"statusCode": 200, "body": f"Audio {object_key} converted to AMR"}

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise
