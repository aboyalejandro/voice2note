import os
import psycopg2
import json
from datetime import timedelta
from aws_lambda_powertools import Logger
import subprocess

# Setup logging
logger = Logger(service="v2n_audio_metadata_processing")


def get_audio_metadata(input_file, ffmepg_path):
    """
    Extract metadata from an audio file using ffmpeg.
    """
    try:
        result = subprocess.run(
            [ffmepg_path, "-i", input_file, "-hide_banner"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )

        # Parse metadata from stderr (ffmpeg outputs to stderr for this command)
        metadata = {}
        for line in result.stderr.split("\n"):
            if "Duration" in line:
                parts = line.split(", ")
                metadata["duration"] = parts[0].split("Duration: ")[1].strip()
                metadata["bit_rate"] = parts[-1].split("bitrate: ")[1].strip()
            if "Stream" in line and "Audio" in line:
                metadata["audio_details"] = line.strip()

        metadata["size"] = os.path.getsize(input_file)
        return metadata
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        raise


def save_metadata_to_postgresql(
    user_id, audio_key, metadata, user, password, db, host, port
):
    try:
        with psycopg2.connect(
            host=host, database=db, user=user, password=password, port=port
        ) as conn:
            with conn.cursor() as cur:
                query = f"""
                UPDATE user_{user_id}.audios
                SET metadata = %s
                WHERE audio_key = %s;
                """
                cur.execute(query, (json.dumps(metadata), audio_key))
                conn.commit()
                logger.info(f"Metadata updated in PostgreSQL for user_{user_id}.audios")
    except Exception as e:
        logger.error(f"Error saving metadata to PostgreSQL: {e}")
        raise
