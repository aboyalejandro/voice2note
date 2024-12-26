from fasthtml.common import *
import boto3
import os
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()

# AWS S3 Configuration
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION")

# PostgreSQL Configuration
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
)
cursor = conn.cursor()

# Initialize FastHTML app
app, rt = fast_app()


@rt("/")
def home():
    return Html(
        Head(Title("Voice2Note")),
        Body(
            Div(
                "Voice2Note",
                style="color: navy; font-size: 2rem; font-weight: bold; text-align: center;",
            ),
            P(
                "Find your transcribed notes effortlessly.",
                style="color: navy; font-size: 1rem; text-align: center;",
            ),
            Div(
                Div(
                    Input(
                        type="file",
                        id="uploadInput",
                        accept="audio/wav",
                        style="display: none;",
                    ),
                    Button(
                        I(cls="fas fa-file-audio"),
                        id="upload",
                        cls="upload-btn",
                        title="Upload Audio",
                    ),
                    Button(
                        I(cls="fas fa-microphone"),
                        id="start",
                        cls="record-btn",
                        title="Start Recording",
                    ),
                    Button(
                        I(cls="fas fa-stop-circle"),
                        id="stop",
                        cls="stop-btn",
                        title="Stop Recording",
                        disabled=True,
                    ),
                    cls="controls",
                ),
                Div(
                    P(
                        "Recording: 0:00",
                        id="recordTimer",
                        style="color: navy; font-size: 1.2rem; margin-top: 10px; display: none;",
                    ),
                    Audio(id="audioPlayback", controls=True, cls="audio-player"),
                    P("", id="audioDuration", style="color: navy; margin-top: 10px;"),
                    cls="audio-wrapper",
                ),
                Div(
                    P(
                        "Is the audio okay? You can save it or record a new one that will override the current one.",
                        style="color: navy; margin-top: 20px;",
                    ),
                    Div(
                        Button("Save Audio", id="save", cls="save-btn", disabled=True),
                        A(
                            Button("See Notes", cls="notes-btn"),
                            href="/notes",
                        ),
                        style="display: flex; gap: 10px; justify-content: center;",
                    ),
                    cls="save-container",
                ),
                Link(
                    rel="stylesheet",
                    href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css",
                ),
                Style(
                    """
                    body {
                        font-family: Arial, sans-serif;
                        text-align: center;
                        background-color: white;
                        color: navy;
                        padding: 20px;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        justify-content: center;
                        height: 100vh;
                        margin: 0;
                    }
                    .controls {
                        margin: 20px 0;
                    }
                    .record-btn, .stop-btn, .upload-btn {
                        font-size: 40px;
                        background: none;
                        border: none;
                        cursor: pointer;
                        padding: 10px;
                        margin: 0 10px;
                        color: navy;
                    }
                    .record-btn:hover {
                        color: red;
                    }
                    .upload-btn:hover {
                        color: #004080;
                    }
                    .stop-btn:hover {
                        color: #ff8000;
                    }
                    .stop-btn[disabled] {
                        color: #ccc;
                        cursor: not-allowed;
                    }
                    .audio-wrapper {
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                        align-items: center;
                        margin-top: 20px;
                    }
                    .audio-player {
                        margin-top: 20px;
                        width: 100%;
                        max-width: 400px;
                        border: 2px solid navy;
                        border-radius: 10px;
                        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
                        background-color: #f9f9f9;
                    }
                    .save-container {
                        margin-top: 20px;
                    }
                    .save-btn {
                        font-size: 16px;
                        padding: 10px 20px;
                        background-color: navy;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    }
                    .save-btn[disabled] {
                        background-color: #ccc;
                        cursor: not-allowed;
                    }
                    .save-btn:hover:not([disabled]) {
                        background-color: #004080;
                    }
                    .notes-btn {
                        font-size: 16px;
                        padding: 10px 20px;
                        background-color: navy;
                        color: white;
                        border: none;
                        border-radius: 5px;
                        cursor: pointer;
                    }
                    .notes-btn:hover {
                        background-color: #004080;
                    }
                    """
                ),
                Script(
                    """
                    let mediaRecorder;
                    let audioChunks = [];
                    let recordInterval;

                    document.getElementById('upload').addEventListener('click', () => {
                        document.getElementById('uploadInput').click();
                    });

                    document.getElementById('uploadInput').addEventListener('change', (event) => {
                        const file = event.target.files[0];
                        if (file) {
                            const audioUrl = URL.createObjectURL(file);
                            const audioPlayback = document.getElementById('audioPlayback');
                            audioPlayback.src = audioUrl;
                            
                            window.audioBlob = file;
                            window.audioType = 'uploaded';
                            
                            document.getElementById('save').disabled = false;
                        }
                    });

                    document.getElementById('start').addEventListener('click', () => {
                        navigator.mediaDevices.getUserMedia({ audio: true })
                            .then(stream => {
                                mediaRecorder = new MediaRecorder(stream);

                                mediaRecorder.ondataavailable = event => {
                                    audioChunks.push(event.data);
                                };

                                mediaRecorder.onstop = () => {
                                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                                    audioChunks = [];
                                    const audioUrl = URL.createObjectURL(audioBlob);
                                    const audioPlayback = document.getElementById('audioPlayback');
                                    audioPlayback.src = audioUrl;

                                    clearInterval(recordInterval);
                                    document.getElementById('recordTimer').style.display = 'none';

                                    document.getElementById('save').disabled = false;

                                    window.audioBlob = audioBlob;
                                    window.audioType = 'recorded';
                                };

                                mediaRecorder.start();
                                document.getElementById('start').disabled = true;
                                document.getElementById('stop').disabled = false;

                                const timerElement = document.getElementById('recordTimer');
                                timerElement.style.display = 'block';
                                let seconds = 0;
                                recordInterval = setInterval(() => {
                                    seconds++;
                                    const minutes = Math.floor(seconds / 60);
                                    const displaySeconds = seconds % 60;
                                    timerElement.textContent = `Recording: ${minutes}:${displaySeconds < 10 ? '0' : ''}${displaySeconds}`;
                                }, 1000);
                            });
                    });

                    document.getElementById('stop').addEventListener('click', () => {
                        mediaRecorder.stop();
                        document.getElementById('start').disabled = false;
                        document.getElementById('stop').disabled = true;
                    });

                    document.getElementById('save').addEventListener('click', () => {
                        const audioBlob = window.audioBlob;
                        const audioType = window.audioType;
                        
                        if (!audioBlob) {
                            alert('No audio to save!');
                            return;
                        }

                        const formData = new FormData();
                        const timestamp = Math.floor(Date.now() / 1000);
                        const filename = `recording_${timestamp}.wav`;
                        formData.append('audio_file', audioBlob, filename);
                        formData.append('audio_type', audioType);

                        fetch('/save-audio', {
                            method: 'POST',
                            body: formData,
                        }).then(response => {
                            if (response.ok) {
                                response.json().then(data => {
                                    alert(`Audio saved successfully! It will show up in the Notes page shortly.`);
                                });
                            } else {
                                alert('Failed to save audio.');
                            }
                        });
                    });
                    """
                ),
            ),
        ),
    )


@rt("/notes")
def notes(start_date: str = None, end_date: str = None):
    # Base query
    query = """
        SELECT 
            audios.audio_key,
            TO_CHAR(audios.created_at, 'MM/DD') as note_date,
            COALESCE(transcription->>'note_title','Transcribing note...') as note_title,
            COALESCE(transcription->>'summary_text','Your audio is being transcribed. It will show up in here when is finished.') as note_summary
        FROM audios
        LEFT JOIN transcripts
        ON audios.audio_key = transcripts.audio_key
        WHERE user_id = %s
    """
    query_params = [1]  # Base parameter (user_id)

    # Add date filtering if dates are provided
    if start_date and end_date:
        query += " AND DATE(audios.created_at) BETWEEN %s AND %s"
        query_params.extend([start_date, end_date])
    elif start_date:
        query += " AND DATE(audios.created_at) >= %s"
        query_params.append(start_date)
    elif end_date:
        query += " AND DATE(audios.created_at) <= %s"
        query_params.append(end_date)

    query += " ORDER BY audios.created_at DESC"

    cursor.execute(query, query_params)
    notes = cursor.fetchall()

    # Create date search form
    date_search = Div(
        Form(
            Div(
                Div(
                    Label("From:", cls="date-label"),
                    Input(
                        type="date",
                        name="start_date",
                        cls="date-input",
                        value=start_date or "",
                    ),
                    cls="date-field",
                ),
                Div(
                    Label("To:", cls="date-label"),
                    Input(
                        type="date",
                        name="end_date",
                        cls="date-input",
                        value=end_date or "",
                    ),
                    cls="date-field",
                ),
                Button("Search", type="submit", cls="search-btn"),
                Button("Clear", type="button", cls="clear-btn", onclick="clearDates()"),
                cls="date-search-container",
            ),
            method="GET",
            cls="date-form",
        ),
        cls="search-wrapper",
    )

    note_cards = [
        Div(
            Div(
                Div(
                    P(note[1], cls="note-date"),
                    P(note[2], cls="note-title"),
                    cls="note-info",
                ),
                cls="note-header",
            ),
            P(note[3], cls="note-preview"),
            Div(
                A(
                    Button("View Note", cls="view-btn"),
                    href=f"/note_{note[0]}",
                ),
                style="text-align: right; margin-top: 10px;",
            ),
            cls="note",
        )
        for note in notes
    ]

    return Html(
        Head(
            Title("Your Notes - Voice2Note"),
            Style(
                """
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f9f9f9;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }
                .container {
                    width: 90%;
                    max-width: 800px;
                    background-color: #ffffff;
                    padding: 20px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    border-radius: 8px;
                    overflow-y: auto;
                    max-height: 90vh;
                }
                .back-button {
                    display: inline-block;
                    margin-top: 40px;
                    margin-bottom: 20px;
                    font-size: 16px;
                    color: #ffffff;
                    background-color: navy;
                    padding: 10px 15px;
                    text-decoration: none;
                    border-radius: 4px;
                }
                .back-button:hover {
                    background-color: #004080;
                }
                .title {
                    font-size: 24px;
                    font-weight: bold;
                    color: navy;
                    margin-bottom: 15px;
                }
                .note {
                    display: flex;
                    flex-direction: column;
                    background-color: #f3f3f3;
                    padding: 10px;
                    border-radius: 8px;
                    margin-bottom: 10px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.0.1);
                }
                .note-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 5px;
                    color: #333;
                }
                .note-info {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .note-title {
                    color: navy;
                    font-weight: bold;
                    font-size: 1.2em;
                    margin: 0;
                }
                .note-date {
                    color: #666;
                    font-size: 0.9em;
                    margin: 0;
                }
                .note-preview {
                    color: #666;
                    font-size: 14px;
                }
                .view-btn {
                    font-size: 14px;
                    padding: 8px 16px;
                    background-color: navy;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                .view-btn:hover {
                    background-color: #004080;
                }
                .search-wrapper {
                    margin-bottom: 20px;
                    width: 100%;
                }
                .date-form {
                    width: 100%;
                }
                .date-search-container {
                    display: flex;
                    gap: 15px;
                    align-items: center;
                    justify-content: flex-end;
                    padding: 15px;
                    background-color: #f3f3f3;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                .date-field {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .date-label {
                    color: navy;
                    font-weight: 500;
                }
                .date-input {
                    padding: 8px;
                    border: 1px solid navy;
                    border-radius: 4px;
                    color: #333;
                }
                .search-btn {
                    padding: 8px 16px;
                    background-color: navy;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                .search-btn:hover {
                    background-color: #004080;
                }
                .clear-btn {
                    padding: 8px 16px;
                    background-color: #666;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }
                .clear-btn:hover {
                    background-color: #555;
                }
                """
            ),
            Script(
                """
                function clearDates() {
                    document.querySelector('input[name="start_date"]').value = '';
                    document.querySelector('input[name="end_date"]').value = '';
                    window.location.href = '/notes';
                }
                """
            ),
        ),
        Body(
            Div(
                A("\u2190 Back", href="/", cls="back-button"),
                Div(H1("Your Last Notes", cls="title")),
                Div(date_search, *note_cards, cls="container"),
            )
        ),
    )


@rt("/note_{audio_key}")
def note_detail(audio_key: str):
    cursor.execute(
        """
        SELECT 
            audios.audio_key,
            TO_CHAR(audios.created_at, 'MM/DD') as note_date,
            COALESCE(transcription->>'note_title','Transcribing note...') as note_title,
            COALESCE(transcription->>'transcript_text','Your audio is being transcribed. It will show up in here when is finished.') as note_transcription
        FROM audios
        LEFT JOIN transcripts
        ON audios.audio_key = transcripts.audio_key
        WHERE audios.audio_key = %s
        """,
        (audio_key,),
    )
    note = cursor.fetchone()

    return Html(
        Head(
            Title("Note Details - Voice2Note"),
            Style(
                """
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f9f9f9;
                    margin: 0;
                    padding: 0;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                }
                .container {
                    width: 90%;
                    max-width: 800px;
                    background-color: #ffffff;
                    padding: 20px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    border-radius: 8px;
                    overflow-y: auto;
                    max-height: 90vh;
                }
                .back-button {
                    display: inline-block;
                    margin-top: 40px;
                    margin-bottom: 20px;
                    font-size: 16px;
                    color: #ffffff;
                    background-color: navy;
                    padding: 10px 15px;
                    text-decoration: none;
                    border-radius: 4px;
                }
                .back-button:hover {
                    background-color: #004080;
                }
                .title {
                    font-size: 24px;
                    font-weight: bold;
                    color: navy;
                    margin-bottom: 15px;
                }
                .note {
                    display: flex;
                    flex-direction: column;
                    background-color: #f3f3f3;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 10px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                .note-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 15px;
                    color: #333;
                    width: 100%;
                }
                .note-info {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }
                .note-title {
                    color: navy;
                    font-weight: bold;
                    font-size: 1.2em;
                    margin: 0;
                }
                .note-date {
                    color: #666;
                    font-size: 0.9em;
                    margin: 0;
                }
                .note-transcription {
                    color: #333;
                    font-size: 16px;
                    line-height: 1.6;
                    white-space: pre-wrap;
                }
                """
            ),
        ),
        Body(
            Div(
                A("\u2190 Back to Notes", href="/notes", cls="back-button"),
                Div(
                    Div(
                        Div(
                            Div(
                                P(note[1], cls="note-date"),
                                P(note[2], cls="note-title"),
                                cls="note-info",
                            ),
                            cls="note-header",
                        ),
                        P(note[3], cls="note-transcription"),
                        cls="note",
                    ),
                    cls="container",
                ),
            )
        ),
    )


@rt("/save-audio")
async def save_audio(audio_file: UploadFile, audio_type: str = Form(...)):
    try:
        # Generate S3 file name
        timestamp = int(datetime.now().timestamp())
        prefix = "audios"
        user_id = 1
        s3_key = f"{prefix}/{user_id}_{timestamp}.wav"
        audio_key = f"{user_id}_{timestamp}"

        # Generate S3 URL
        s3_url = f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

        logging.info(f"Saving {audio_type} audio file with key: {audio_key}")

        # Insert record into PostgreSQL with audio_type
        try:
            cursor.execute(
                "INSERT INTO audios (audio_key, user_id, s3_object_url, audio_type, created_at) VALUES (%s, %s, %s, %s, %s) RETURNING audio_key",
                (audio_key, user_id, s3_url, audio_type, datetime.now()),
            )
            conn.commit()
            logging.info(f"Database record created for audio_key: {audio_key}")
        except Exception as e:
            logging.error(
                f"Database insertion failed for audio_key {audio_key}: {str(e)}"
            )
            raise

        # Upload to S3
        try:
            s3.upload_fileobj(audio_file.file, AWS_S3_BUCKET, s3_key)
            logging.info(f"Audio file uploaded to S3: {s3_key}")
        except Exception as e:
            logging.error(f"S3 upload failed for key {s3_key}: {str(e)}")
            raise

        return {"audio_key": cursor.fetchone()[0]}

    except Exception as e:
        logging.error(f"Error in save_audio endpoint: {str(e)}")
        raise


serve()
