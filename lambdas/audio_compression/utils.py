from aws_lambda_powertools import Logger
import subprocess
import psycopg2
import json

# Setup logging
logger = Logger(service="v2n_audio_compression")


def convert_to_amr(input_file, output_file, ffmpeg_path):
    """
    Convert a WAV audio file to AMR format using ffmpeg, suppressing logs.
    """
    try:
        subprocess.run(
            [
                ffmpeg_path,
                "-i",
                input_file,
                "-ar",
                "8000",
                "-ab",
                "12.2k",
                "-ac",
                "1",
                output_file,
            ],
            stdout=subprocess.DEVNULL,  # Suppress standard output
            stderr=subprocess.DEVNULL,  # Suppress error output
            check=True,
        )
        logger.info(f"Converted {input_file} to {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error converting to AMR: {e}")
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
