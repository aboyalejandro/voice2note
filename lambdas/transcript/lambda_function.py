import os
import boto3
from utils import validate_file_extension, transcribe_audio, publish_to_sns
from aws_lambda_powertools import Logger

# Setup logging
logger = Logger(service="v2n_transcript")

# AWS clients
s3_client = boto3.client("s3")
transcribe_client = boto3.client("transcribe")
sns_client = boto3.client("sns")
sns_topic_arn = os.getenv("SNS_TOPIC_ARN")


# Lambda handler
def lambda_handler(event, context):
    try:
        # Extract bucket and object info from event
        bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
        object_key = event["Records"][0]["s3"]["object"]["key"]

        logger.info(f"New file detected: {object_key} in bucket {bucket_name}")

        # Validate path structure
        path_parts = object_key.split("/")
        if (
            len(path_parts) != 4
            or not path_parts[0].startswith("user_")
            or path_parts[1] != "audios"
            or path_parts[2] != "raw"
        ):
            raise ValueError(
                "Invalid path structure. Expected: user_{user_id}/audios/raw/filename"
            )

        # Validate file extension
        is_valid, media_format = validate_file_extension(object_key)
        if not is_valid:
            raise ValueError(
                f"Invalid file extension for {object_key}. Only .mp3, .wav, and .webm are supported."
            )

        # Extract user_id for logging
        user_id = path_parts[0].replace("user_", "")
        audio_key = path_parts[3].replace(f".{media_format}", "")
        logger.info(f"Processing audio {audio_key} for user {user_id}")

        # Start transcription with dynamic media format
        transcription_response = transcribe_audio(
            bucket_name, object_key, transcribe_client, media_format
        )

        logger.info(
            f"Transcription job started for user {user_id}: {transcription_response}"
        )

        # Publish Payload
        publish_to_sns(bucket_name, object_key, sns_client, sns_topic_arn)

        return {"statusCode": 200, "body": f"Processing started for {object_key}"}

    except Exception as e:
        logger.error(f"Error in processing: {e}")
        raise
