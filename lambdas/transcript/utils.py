import boto3
from aws_lambda_powertools import Logger

# Setup logging
logger = Logger(service="v2n_transcript")


# Transcription function in AWS Transcribe
def transcribe_audio(bucket_name: str, object_key: str, client):
    try:
        # Parse path components from the new structure
        path_parts = object_key.split("/")  # ['user_1', 'audios', '1_timestamp.wav']
        user_path = path_parts[0]  # user_1
        audio_key = path_parts[2].replace(".wav", "")  # 1_timestamp

        job_name = f"v2n_transcribe_job_{audio_key}"
        file_uri = f"s3://{bucket_name}/{object_key}"

        logger.info(
            f"Starting transcription job for {job_name}",
        )

        # Store transcript in user's folder structure
        output_key = f"{user_path}/transcripts/raw/{audio_key}.json"

        response = client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": file_uri},
            MediaFormat="wav",
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


# Publish to SNS
def publish_to_sns(bucket_name, object_key, sns_topic_arn):
    message = {"bucket_name": bucket_name, "object_key": object_key}
    sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Message=json.dumps(message),
        Subject=f"New audio available in {object_key}",
    )
    logger.info(f"Published message to SNS: {message}")
