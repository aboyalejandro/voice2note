from aws_lambda_powertools import Logger
import subprocess
import psycopg2
import json
import os

# Setup logging
logger = Logger(service="v2n_audio_compression")


def validate_file_extension(object_key):
    valid_extensions = [".mp3", ".wav", ".webm"]
    _, extension = os.path.splitext(object_key)
    return extension.lower() in valid_extensions


def convert_to_webm(input_file, output_file, ffmpeg_path):
    """
    Convert audio file to WebM format using ffmpeg.
    """
    try:
        subprocess.run(
            [ffmpeg_path, "-i", input_file, "-c:a", "libopus", output_file],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        logger.info(f"Converted {input_file} to {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error converting to WebM: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during conversion: {e}")
        raise


def update_metadata(user_id, audio_key, metadata, user, password, db, host, port):
    try:
        with psycopg2.connect(
            host=host, database=db, user=user, password=password, port=port
        ) as conn:
            with conn.cursor() as cur:
                # Correct path for the key you want to update
                query = f"""
                UPDATE user_{user_id}.audios
                SET metadata = jsonb_set(metadata, '{{s3_compressed_audio_url}}', %s::jsonb)
                WHERE audio_key = %s;
                """
                # Metadata should be a JSON object; stringify it before sending
                metadata_json = json.dumps(metadata)
                cur.execute(query, (metadata_json, audio_key))
                conn.commit()
                logger.info(f"Metadata updated in PostgreSQL for user_{user_id}.audios")
    except Exception as e:
        logger.error(f"Error saving metadata to PostgreSQL: {e}")
        raise
