import os
import boto3
from openai import OpenAI
from utils import (
    get_transcript,
    run_llm,
    export_summary,
    save_to_postgresql,
    process_and_save_vectors,
)
from aws_lambda_powertools import Logger

# Setup logging
logger = Logger(service="v2n_summarize")

# AWS clients
s3_client = boto3.client("s3")

# ENVs AI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
open_ai_client = OpenAI(api_key=OPENAI_API_KEY)

# ENVs Database
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

# PROMPTS
gpt_rol = "You are a voice note summarizing assistant."
gpt_prompt_summary = """
    You are a voice note summarizing assistant that provides summaries of no more than 2 sentences.
    The summary must address the user directly (e.g., "You are planning a holiday...").
    Ensure the output is in the same language as the text input. Here's your text:
    """
gpt_prompt_title = """
    You are a voice note summarizing assistant that provides titles of no more than 5 words.
    Ensure the output is in the same language as the text input and omit quotation marks. Here's your text:
    """


def lambda_handler(event, context):
    try:
        # Extract bucket and object info from event
        bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
        object_key = event["Records"][0]["s3"]["object"]["key"]

        logger.info(f"New JSON detected: {object_key} in bucket {bucket_name}")

        # Validate path
        if "transcripts/raw/" not in object_key:
            logger.info(f"Skipping: {object_key} (not in transcripts/raw/).")
            return

        # Extract assets
        path_parts = object_key.split("/")
        user_path = path_parts[0]  # user_1
        audio_key = path_parts[3].replace(".json", "")  # file (without extension)

        # Process transcription
        transcript_text = get_transcript(bucket_name, object_key, s3_client)
        summary_text = run_llm(
            transcript_text, gpt_prompt_summary, gpt_rol, open_ai_client
        )
        note_title = run_llm(summary_text, gpt_prompt_title, gpt_rol, open_ai_client)

        # Export processing
        transcript_results = export_summary(
            bucket_name,
            user_path,
            audio_key,
            transcript_text,
            summary_text,
            note_title,
            s3_client,
        )

        # Save to User Schema
        save_to_postgresql(
            user_path,
            audio_key,
            transcript_results,
            DB_HOST,
            DB_NAME,
            DB_USER,
            DB_PASSWORD,
            DB_PORT,
        )

        # Save Vectors for LLM
        process_and_save_vectors(
            user_path,
            audio_key,
            transcript_results[1],
            open_ai_client,
            DB_HOST,
            DB_NAME,
            DB_USER,
            DB_PASSWORD,
            DB_PORT,
        )

    except Exception as e:
        logger.error(f"Error in processing: {e}")
        raise
