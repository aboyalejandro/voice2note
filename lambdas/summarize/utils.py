from datetime import datetime
import json
import psycopg2
from aws_lambda_powertools import Logger

# Setup logging
logger = Logger(service="v2n_summarize")


def get_transcript(bucket_name: str, object_key: str, s3_client):
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    transcription_result = json.loads(response["Body"].read().decode("utf-8"))
    transcript_text = transcription_result["results"]["transcripts"][0]["transcript"]
    return transcript_text


def run_llm(input: str, instruction: str, role: str, client):
    prompt = f"{instruction}:\n\n{input}"
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"{role}"},
            {"role": "user", "content": prompt},
        ],
    )
    logger.info(f'Running LLM for transcript for input "{input[:25]}..."')
    return completion.choices[0].message.content


# Generate JSON output and upload to S3
def export_summary(
    bucket_name: str,
    user_path: str,
    audio_key: str,
    transcript_text: str,
    summary_text: str,
    note_title: str,
    s3_client,
):
    try:
        timestamp = int(datetime.now().timestamp())
        json_file_name = f"{audio_key}_{timestamp}.json"
        json_file_path = f"/tmp/{json_file_name}"

        # Use user's path structure
        output_path = f"{user_path}/transcripts/processed/{json_file_name}"

        json_object = {
            "note_title": note_title,
            "transcript_text": transcript_text,
            "summary_text": summary_text,
        }

        with open(json_file_path, "w") as json_file:
            json.dump(json_object, json_file)

        s3_client.upload_file(json_file_path, bucket_name, output_path)
        logger.info(f"JSON file uploaded to {bucket_name}/{output_path}")

        full_output_path = f"s3://{bucket_name}/{output_path}"

        return [full_output_path, json_object]
    except Exception as e:
        logger.error(f"Error exporting summary: {e}")
        raise


def save_to_postgresql(
    user_path: str,
    audio_key: str,
    transcript_results: dict,
    host: str,
    db: str,
    user: str,
    password: str,
    port: str,
):
    try:
        with psycopg2.connect(
            host=host, database=db, user=user, password=password, port=port
        ) as conn:
            with conn.cursor() as cur:
                # Set schema for this connection
                cur.execute(f"SET search_path TO {user_path}")

                # Insert into transcripts table in user's schema
                query = """
                    INSERT INTO transcripts 
                    (audio_key, s3_object_url, transcription, created_at) 
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                """
                values = (
                    audio_key,
                    transcript_results[0],  # Pass the string directly
                    json.dumps(transcript_results[1]),
                )

                cur.execute(query, values)
                conn.commit()
                logger.info(f"Data saved to PostgreSQL in schema {user_path}")
    except Exception as e:
        logger.error(f"Error saving to PostgreSQL: {e}")
        raise


def process_vectors(
    transcription: dict, client, user_path: str, audio_key: str, conn, cur
):
    """Process and store vectors for transcript text"""
    try:
        transcript_text = transcription.get("transcript_text", "")
        if not transcript_text:
            logger.warn(f"No transcript text found for {audio_key}")
            return

        # Split text into chunks (~1000 chars each)
        words = transcript_text.split()
        chunks = []
        current_chunk = []
        current_length = 0

        for word in words:
            word_length = len(word) + 1  # +1 for space
            if current_length + word_length > 1000:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_length = word_length
            else:
                current_chunk.append(word)
                current_length += word_length

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        # Get embeddings and store them
        cur.execute(f"SET search_path TO {user_path}")

        for chunk in chunks:
            # Get embedding from OpenAI
            response = client.embeddings.create(
                model="text-embedding-ada-002", input=chunk
            )
            embedding = response.data[0].embedding

            # Store in PostgreSQL
            cur.execute(
                """
                INSERT INTO note_vectors 
                    (audio_key, content_chunk, embedding)
                VALUES (%s, %s, %s)
                """,
                (audio_key, chunk, json.dumps(embedding)),
            )

        conn.commit()
        logger.info(f"Stored {len(chunks)} vectors for {audio_key}")

    except Exception as e:
        logger.error(f"Error processing vectors: {e}")
        raise


def process_and_save_vectors(
    user_path: str,
    audio_key: str,
    transcription: dict,
    client,  # OpenAI client
    host: str,
    db: str,
    user: str,
    password: str,
    port: str,
):
    """Process and store vectors as a separate operation"""
    try:
        with psycopg2.connect(
            host=host, database=db, user=user, password=password, port=port
        ) as conn:
            with conn.cursor() as cur:
                process_vectors(transcription, client, user_path, audio_key, conn, cur)
                logger.info(f"Vectors saved for audio_key {audio_key}")
    except Exception as e:
        logger.error(f"Error saving vectors: {e}")
        raise
