from aws_lambda_powertools import Logger
import subprocess
import psycopg2
import json
import os

# Setup logging
logger = Logger(service="v2n_audio_processing")


def validate_file_extension(object_key):
    """
    Validate file extension and return extension type.
    """
    valid_extensions = [".mp3", ".wav", ".webm"]
    _, extension = os.path.splitext(object_key)
    return extension.lower() in valid_extensions, extension.lower().replace(".", "")


def reencode_webm(input_file, output_file, ffmpeg_path):
    """
    Re-encode .webm file to ensure proper metadata.
    """
    try:
        subprocess.run(
            [
                ffmpeg_path,
                "-i",
                input_file,
                "-map_metadata",
                "-1",  # Clear metadata
                "-c:v",
                "copy",
                "-c:a",
                "libopus",
                output_file,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        logger.info(f"Re-encoded {input_file} to {output_file}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error re-encoding .webm file: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during re-encoding: {e}")
        raise


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


def get_audio_metadata(input_file, ffmpeg_path):
    """
    Extract metadata from an audio file using ffmpeg, re-encode if metadata is missing.
    """
    try:
        result = subprocess.run(
            [ffmpeg_path, "-i", input_file, "-hide_banner"],
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
        )

        metadata = {}
        for line in result.stderr.split("\n"):
            if "Duration" in line:
                parts = line.split(", ")
                metadata["duration"] = (
                    parts[0].split("Duration: ")[1].strip()
                    if "Duration:" in parts[0]
                    else "00:00:00"
                )
                metadata["bit_rate"] = (
                    parts[-1].split("bitrate: ")[1].strip()
                    if "bitrate:" in parts[-1]
                    else "N/A"
                )
            if "Stream" in line and "Audio" in line:
                metadata["audio_details"] = str(line.strip())

        metadata["size"] = os.path.getsize(input_file)

        # Check if duration is missing, indicating a metadata issue
        if metadata.get("duration") == "00:00:00":
            raise ValueError("Missing duration in metadata")

        return metadata
    except Exception as e:
        logger.error(f"Error extracting metadata: {e}")
        raise


def save_to_postgresql(user_id, audio_key, metadata, user, password, db, host, port):
    """
    Save combined metadata (audio metadata + s3 url) to PostgreSQL.
    """
    try:
        # Ensure metadata is JSON-serializable
        metadata_json = json.dumps(metadata)

        with psycopg2.connect(
            host=host, database=db, user=user, password=password, port=port
        ) as conn:
            with conn.cursor() as cur:
                query = f"""
                UPDATE user_{user_id}.audios
                SET metadata = %s
                WHERE audio_key = %s
                RETURNING metadata;
                """
                cur.execute(query, (metadata_json, audio_key))
                updated_row = cur.fetchone()
                conn.commit()

                if cur.rowcount == 0:
                    raise ValueError(f"No record found for audio_key: {audio_key}")

                logger.info(f"Metadata updated in PostgreSQL for user_{user_id}.audios")
                logger.info(
                    f"Updated metadata: {updated_row[0] if updated_row else 'No data returned'}"
                )

    except Exception as e:
        logger.error(f"Error saving to PostgreSQL: {e}")
        raise
