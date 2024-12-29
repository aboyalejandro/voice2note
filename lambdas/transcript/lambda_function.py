import boto3
from utils import transcribe_audio
from aws_lambda_powertools import Logger

# Setup logging
logger = Logger(service="v2n_transcript")

# AWS clients
s3_client = boto3.client("s3")
transcribe_client = boto3.client("transcribe")


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
            len(path_parts) != 3
            or not path_parts[0].startswith("user_")
            or path_parts[1] != "audios"
        ):
            raise ValueError(
                f"Invalid path structure: {object_key}. Expected: user_X/audios/filename.wav"
            )

        # Extract user_id for logging
        user_id = path_parts[0].replace("user_", "")
        audio_key = path_parts[2].replace(".wav", "")
        logger.info(f"Processing audio {audio_key} for user {user_id}")

        # Start transcription
        transcription_response = transcribe_audio(
            bucket_name, object_key, transcribe_client
        )

        logger.info(
            f"Transcription job started for user {user_id}: {transcription_response}"
        )
        return {"statusCode": 200, "body": f"Processing started for {object_key}"}

    except Exception as e:
        logger.error(f"Error in processing: {e}")
        raise
