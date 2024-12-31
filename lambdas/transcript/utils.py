import boto3
from datetime import datetime
import json
from aws_lambda_powertools import Logger

# Setup logging
logger = Logger(service="v2n_transcript")


def validate_file_extension(object_key):
    valid_extensions = [".mp3", ".wav", ".webm"]
    _, extension = os.path.splitext(object_key)
    return extension.lower() in valid_extensions, extension.lower().replace(".", "")


# Transcription function in AWS Transcribe
import os
import boto3
from aws_lambda_powertools import Logger

# Setup logging
logger = Logger(service="v2n_transcript")

# AWS clients
s3_client = boto3.client("s3")
transcribe_client = boto3.client("transcribe")
sns_client = boto3.client("sns")
sns_topic_arn = os.getenv("SNS_TOPIC_ARN")


def validate_file_extension(object_key):
    valid_extensions = [".mp3", ".wav", ".webm"]
    _, extension = os.path.splitext(object_key)
    return extension.lower() in valid_extensions, extension.lower().replace(".", "")


def transcribe_audio(bucket_name, object_key, client, media_format):
    """
    Transcription function in AWS Transcribe
    """
    try:
        # Parse path components from the new structure
        path_parts = object_key.split(
            "/"
        )  # ['user_1', 'audios', 'raw', '1_timestamp.webm']
        user_path = path_parts[0]  # user_1
        audio_key = path_parts[3].replace(f".{media_format}", "")  # 1_timestamp

        job_name = f"v2n_transcribe_job_{audio_key}"
        file_uri = f"s3://{bucket_name}/{object_key}"

        logger.info(f"Starting transcription job for {job_name}")

        # Store transcript in user's folder structure
        output_key = f"{user_path}/transcripts/raw/{audio_key}.json"

        response = client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": file_uri},
            MediaFormat=media_format,
            IdentifyLanguage=True,
            LanguageOptions=["en-US", "es-ES"],
            OutputBucketName=bucket_name,
            OutputKey=output_key,
        )

        logger.info(
            f"Transcription configured to output to: s3://{bucket_name}/{output_key}"
        )
        return response

    except Exception as e:
        logger.error(f"Error during transcription: {e}")
        raise


def publish_to_sns(bucket_name, object_key, sns_client, sns_topic_arn):
    """
    Publish to SNS
    """
    try:
        message = {"bucket_name": bucket_name, "object_key": object_key}
        sns_client.publish(
            TopicArn=sns_topic_arn,
            Message=json.dumps(
                {"bucket_name": f"{bucket_name}", "object_key": f"{object_key}"}
            ),
            Subject=f"New audio available in {object_key}",
        )
        logger.info("SNS message published successfully.")
    except Exception as e:
        logger.error(f"Error publishing SNS message: {e}")
        raise


# Publish to SNS
def publish_to_sns(bucket_name, object_key, sns_client, sns_topic_arn):
    try:
        message = {"bucket_name": bucket_name, "object_key": object_key}
        sns_client.publish(
            TopicArn=sns_topic_arn,
            Message=json.dumps(
                {"bucket_name": f"{bucket_name}", "object_key": f"{object_key}"}
            ),
            Subject=f"New audio available in {object_key}",
        )
        logger.info("SNS message published successfully.")
    except Exception as e:
        logger.error(f"Error publishing SNS message: {e}")
        raise
