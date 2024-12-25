import os
import boto3
import json
from datetime import datetime
from openai import OpenAI
from utils import get_transcript, run_llm, export_summary, save_to_postgresql

# AWS clients
s3_client = boto3.client("s3")

# ENVs AI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
open_ai_client = OpenAI(api_key=OPENAI_API_KEY)

# ENVs Database
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")


# PROMPTS
gpt_rol = "You are a voice note summarizing assistant."
gpt_prompt_summary = "You are a voice note summarizing assistant that provides summaries of no more than 2 sentences with simple language, here's your text"
gpt_prompt_title = "You are a voice note summarizing assistant that provides titles for note summaries of no more than 3 words of simple language, here's your text"

# Lambda handler
def lambda_handler(event, context): 
    try:
        # Extract bucket and object info from event
        bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
        object_key = event["Records"][0]["s3"]["object"]["key"]
        
        print(f"New file detected: {object_key} in bucket {bucket_name}")

        transcript_text = get_transcript(bucket_name, object_key, s3_client)
        summary_text = run_llm(transcript_text, gpt_prompt_summary, gpt_rol, open_ai_client)
        note_title = run_llm(summary_text, gpt_prompt_title, gpt_rol, open_ai_client)
        
        audio_key = object_key.split('/')[-1].replace('.json', '')
        user_id = audio_key.split('_')[0]

        transcript_results = export_summary(bucket_name, user_id, audio_key, transcript_text ,summary_text, note_title, s3_client) 
    
        # Save transcript to PostgreSQL
        transcript_query = (
            "INSERT INTO transcripts (audio_key, s3_object_url, transcription, created_at) VALUES (%s, %s, %s, %s)"
        )
        transcript_values = (audio_key, transcript_results['s3_object_url'], json.dumps(transcript_results), datetime.now())
        save_to_postgresql(transcript_query, transcript_values, DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT)
    
    except Exception as e:
        print(f"Error in processing: {e}")
        raise