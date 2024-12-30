from aws_lambda_powertools import Logger
import subprocess

# Setup logging
logger = Logger(service="v2n_audio_compression")


def convert_to_amr(input_file, output_file, ffmpeg_path):
    """
    Convert a WAV audio file to AMR format using ffmpeg.
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
            check=True,
        )
        logger.info(f"Converted {input_file} to {output_file}")
    except Exception as e:
        logger.error(f"Error converting to AMR: {e}")
        raise
