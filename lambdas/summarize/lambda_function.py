import os
import boto3
import json
from datetime import datetime
from openai import OpenAI
from utils import get_transcript, run_llm, export_summary, save_to_postgresql

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
    Please, the summary should talk to the user e.g. "You are planning a holiday..." 
    Provide the output in the language of the text input, here's your text
    """
gpt_prompt_title = """
    You are a voice note summarizing assistant that provides titles of no more than 5 words. 
    Provide the output in the language of the text input, here's your text
    """


def lambda_handler(event, context):
    try:
        # Extract bucket and object info from event
        bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
        object_key = event["Records"][0]["s3"]["object"]["key"]

        print(f"New JSON detected: {object_key} in bucket {bucket_name}")

        # 1. Verificar si el objeto está en la ruta transcripts/raw/
        if "transcripts/raw/" not in object_key:
            print(f"Skipping: {object_key} (not in transcripts/raw/).")
            return

        # 2. Verificar estructura esperada: user_X/transcripts/raw/filename.json
        path_parts = object_key.split(
            "/"
        )  # ej. ['user_1','transcripts','raw','archivo.json']
        if (
            len(path_parts) != 4
            or not path_parts[0].startswith("user_")
            or path_parts[1] != "transcripts"
            or path_parts[2] != "raw"
        ):
            print(f"Skipping: {object_key} (invalid path structure).")
            return

        user_path = path_parts[0]  # user_1
        audio_key = path_parts[3].replace(".json", "")  # archivo (sin extensión)

        # 3. Procesar el transcript
        transcript_text = get_transcript(bucket_name, object_key, s3_client)
        summary_text = run_llm(
            transcript_text, gpt_prompt_summary, gpt_rol, open_ai_client
        )
        note_title = run_llm(summary_text, gpt_prompt_title, gpt_rol, open_ai_client)

        # 4. Exportar a processed/
        transcript_results = export_summary(
            bucket_name,
            user_path,  # Pass full user_path instead of just ID
            audio_key,
            transcript_text,
            summary_text,
            note_title,
            s3_client,
        )

        # 5. Guardar en PostgreSQL (en el schema del usuario)
        save_to_postgresql(
            user_path,  # user_1
            audio_key,
            transcript_results,
            DB_HOST,
            DB_NAME,
            DB_USER,
            DB_PASSWORD,
            DB_PORT,
        )

    except Exception as e:
        print(f"Error in processing: {e}")
        raise
