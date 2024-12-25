import boto3
from datetime import datetime

# Transcription function in AWS Transcribe
def transcribe_audio(
    bucket_name: str,
    object_key: str, 
    client
    ):
    try:
        file_cleaned = object_key.split('/')[1].replace('.wav', '')
        job_name = f'v2n_layer_transcribe_job_{file_cleaned}'
        file_uri = f"s3://{bucket_name}/{object_key}"

        print(f"Starting transcription job for {job_name}")

        response = client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': file_uri},
            MediaFormat='wav',
            IdentifyLanguage=True, 
            LanguageOptions=['en-US', 'es-ES'], 
            OutputBucketName=bucket_name,
            OutputKey=f"transcripts/raw/{file_cleaned}.json"
        )
        return f"Transcription job started: {response}"

    except Exception as e:
        print(f"Error during transcription: {e}")
        raise