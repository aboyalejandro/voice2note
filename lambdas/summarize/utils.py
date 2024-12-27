from datetime import datetime
import json
import psycopg2


def get_transcript(bucket_name: str, object_key: str, s3_client):
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    transcription_result = json.loads(response["Body"].read().decode("utf-8"))
    transcript_text = transcription_result["results"]["transcripts"][0]["transcript"]
    return transcript_text


def run_llm(input: str, instruction: str, role: str, client):
    prompt = f"{instruction}:\n\n{input}"
    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": f"{role}"},
            {"role": "user", "content": prompt},
        ],
    )
    return completion.choices[0].message.content


# Generate JSON output and upload to S3
def export_summary(
    bucket_name: str,
    user_path: str,  # Changed from user_id to user_path
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
            "s3_object_url": f"s3://{bucket_name}/{output_path}",
            "note_title": note_title,
            "transcript_text": transcript_text,
            "summary_text": summary_text,
        }

        with open(json_file_path, "w") as json_file:
            json.dump(json_object, json_file)

        s3_client.upload_file(json_file_path, bucket_name, output_path)
        print(f"JSON file uploaded to {bucket_name}/{output_path}")

        return json_object
    except Exception as e:
        print(f"Error exporting summary: {e}")
        raise


def save_to_postgresql(
    user_path: str,  # New parameter for schema selection
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
                    transcript_results["s3_object_url"],
                    json.dumps(transcript_results),
                )

                cur.execute(query, values)
                conn.commit()
                print(f"Data saved to PostgreSQL in schema {user_path}")
    except Exception as e:
        print(f"Error saving to PostgreSQL: {e}")
        raise
