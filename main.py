from fasthtml.common import *
import boto3
import os
from datetime import datetime
from dotenv import load_dotenv
import psycopg2

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
                    Button("Save Audio", id="save", cls="save-btn", disabled=True),
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
                .record-btn, .stop-btn {
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
                """
                ),
                Script(
                    """
                let mediaRecorder;
                let audioChunks = [];
                let recordInterval;

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

                                // Stop the timer and hide it
                                clearInterval(recordInterval);
                                document.getElementById('recordTimer').style.display = 'none';

                                // Enable Save Button
                                document.getElementById('save').disabled = false;

                                // Store the audioBlob globally for saving later
                                window.audioBlob = audioBlob;
                            };

                            mediaRecorder.start();
                            document.getElementById('start').disabled = true;
                            document.getElementById('stop').disabled = false;

                            // Start the timer
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
                    if (!audioBlob) {
                        alert('No audio to save!');
                        return;
                    }

                    const formData = new FormData();
                    const timestamp = Math.floor(Date.now() / 1000);
                    const filename = `recording_${timestamp}.wav`;
                    formData.append('audio_file', audioBlob, filename);

                    fetch('/save-audio', {
                        method: 'POST',
                        body: formData,
                    }).then(response => {
                        if (response.ok) {
                            response.json().then(data => {
                                alert(`Audio saved succesfully!`);
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


@rt("/save-audio")
async def save_audio(audio_file: UploadFile):
    # Generate S3 file name
    timestamp = int(datetime.now().timestamp())
    prefix = "audios"
    # user_id is by default 1
    user_id = 1
    s3_key = f"{prefix}/{user_id}_{timestamp}.wav"
    audio_key = f"{user_id}_{timestamp}"

    # Generate S3 URL
    s3_url = f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

    # Insert record into PostgreSQL
    cursor.execute(
        "INSERT INTO audios (audio_key, user_id, s3_object_url, created_at) VALUES (%s, %s, %s, %s) RETURNING audio_key",
        (audio_key, user_id, s3_url, datetime.now()),
    )
    conn.commit()

    # Upload to S3
    s3.upload_fileobj(audio_file.file, AWS_S3_BUCKET, s3_key)

    return {"audio_key": cursor.fetchone()[0]}


serve()
