from fasthtml.common import *
import boto3
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import psycopg2
import logging
import json
import bcrypt
import uuid

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


def get_common_styles():
    return """
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
    .auth-container {
        width: 90%;
        max-width: 400px;
        background-color: #ffffff;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-radius: 8px;
    }
    .auth-title {
        font-size: 24px;
        font-weight: bold;
        color: navy;
        text-align: center;
        margin-bottom: 20px;
    }
    .auth-form {
        display: flex;
        flex-direction: column;
        gap: 15px;
    }
    .form-group {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .form-label {
        color: navy;
        font-weight: 500;
    }
    .form-input {
        padding: 10px;
        border: 1px solid navy;
        border-radius: 4px;
        font-size: 16px;
    }
    .form-input:focus {
        outline: none;
        border-color: #004080;
        box-shadow: 0 0 0 2px rgba(0, 64, 128, 0.1);
    }
    .auth-btn {
        font-size: 16px;
        padding: 12px 20px;
        background-color: navy;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        transition: background-color 0.2s;
    }
    .auth-btn:hover {
        background-color: #004080;
    }
    .auth-link {
        text-align: center;
        margin-top: 15px;
        color: #666;
    }
    .auth-link a {
        color: navy;
        text-decoration: none;
        font-weight: 500;
    }
    .auth-link a:hover {
        text-decoration: underline;
    }
    .error-message {
        color: #dc3545;
        background-color: #ffe6e6;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 15px;
        font-size: 14px;
        text-align: center;
    }
    """


def get_logout_button():
    return Div(
        Form(
            Button(
                "Logout",
                type="submit",
                cls="logout-btn",
            ),
            method="POST",
            action="/api/logout",
        ),
        style="position: absolute; top: 20px; right: 20px;",
    )


def get_logout_styles():
    return """
    
    """


@rt("/login")
def login(request: Request):
    return Html(
        Head(
            Title("Login - Voice2Note"),
            Link(
                rel="stylesheet",
                href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css",
            ),
            Style(get_common_styles()),
        ),
        Body(
            Div(
                H1("Login to Voice2Note", cls="auth-title"),
                Form(
                    Div(
                        Label("Username", For="username", cls="form-label"),
                        Input(
                            type="text",
                            name="username",
                            id="username",
                            required=True,
                            cls="form-input",
                            placeholder="Enter your username",
                        ),
                        cls="form-group",
                    ),
                    Div(
                        Label("Password", For="password", cls="form-label"),
                        Input(
                            type="password",
                            name="password",
                            id="password",
                            required=True,
                            cls="form-input",
                            placeholder="Enter your password",
                        ),
                        cls="form-group",
                    ),
                    Button("Login", type="submit", cls="auth-btn"),
                    method="POST",
                    action="/api/login",
                    cls="auth-form",
                ),
                P(
                    "Don't have an account? ",
                    A("Sign up", href="/signup"),
                    cls="auth-link",
                ),
                cls="auth-container",
            )
        ),
    )


@rt("/signup")
def signup(request: Request):
    return Html(
        Head(
            Title("Sign Up - Voice2Note"),
            Link(
                rel="stylesheet",
                href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css",
            ),
            Style(get_common_styles()),
        ),
        Body(
            Div(
                H1("Create Account", cls="auth-title"),
                Form(
                    Div(
                        Label("Username", For="username", cls="form-label"),
                        Input(
                            type="text",
                            name="username",
                            id="username",
                            required=True,
                            cls="form-input",
                            placeholder="Choose a username",
                        ),
                        cls="form-group",
                    ),
                    Div(
                        Label("Password", For="password", cls="form-label"),
                        Input(
                            type="password",
                            name="password",
                            id="password",
                            required=True,
                            cls="form-input",
                            placeholder="Choose a password",
                        ),
                        cls="form-group",
                    ),
                    Button("Create Account", type="submit", cls="auth-btn"),
                    method="POST",
                    action="/api/signup",
                    cls="auth-form",
                ),
                P(
                    "Already have an account? ",
                    A("Login", href="/login"),
                    cls="auth-link",
                ),
                cls="auth-container",
            )
        ),
    )


# API endpoints for authentication
@rt("/api/signup", methods=["POST"])
async def api_signup(request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    # Check if username already exists
    cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        return Html(
            Head(
                Title("Sign Up Error - Voice2Note"),
                Style(get_common_styles()),
            ),
            Body(
                Div(
                    H1("Sign Up Error", cls="auth-title"),
                    P("Username already exists", cls="error-message"),
                    A("Try Again", href="/signup", cls="auth-btn"),
                    cls="auth-container",
                )
            ),
        )

    # Hash password with bcrypt
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    try:
        # Insert new user
        cursor.execute(
            """
            INSERT INTO users (username, hashed_password, created_at)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            RETURNING user_id
            """,
            (username, hashed_password.decode("utf-8")),
        )
        user_id = cursor.fetchone()[0]
        conn.commit()

        # Create session for the new user
        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(days=7)

        cursor.execute(
            """
            INSERT INTO sessions (session_id, user_id, expires_at)
            VALUES (%s, %s, %s)
            """,
            (session_id, user_id, expires_at),
        )
        conn.commit()

        # Redirect with session cookie
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=7 * 24 * 60 * 60,
            secure=True,
            samesite="lax",
        )
        return response

    except Exception as e:
        conn.rollback()
        logging.error(f"Error in signup: {str(e)}")
        return Html(
            Head(
                Title("Sign Up Error - Voice2Note"),
                Style(get_common_styles()),
            ),
            Body(
                Div(
                    H1("Sign Up Error", cls="auth-title"),
                    P("Error creating account. Please try again.", cls="error-message"),
                    A("Try Again", href="/signup", cls="auth-btn"),
                    cls="auth-container",
                )
            ),
        )


@rt("/api/login", methods=["POST"])
async def api_login(request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")

    # Get user from database
    cursor.execute(
        "SELECT user_id, username, hashed_password FROM users WHERE username = %s",
        (username,),
    )
    user = cursor.fetchone()

    if not user:
        return Html(
            Head(Title("Login Error - Voice2Note"), Style(get_common_styles())),
            Body(
                Div(
                    H1("Login Error", cls="auth-title"),
                    P("Invalid username or password", cls="error-message"),
                    A("Try Again", href="/login", cls="auth-btn"),
                    cls="auth-container",
                )
            ),
        )

    try:
        # Verify password
        if not bcrypt.checkpw(password.encode("utf-8"), user[2].encode("utf-8")):
            return Html(
                Head(Title("Login Error - Voice2Note"), Style(get_common_styles())),
                Body(
                    Div(
                        H1("Login Error", cls="auth-title"),
                        P("Invalid username or password", cls="error-message"),
                        A("Try Again", href="/login", cls="auth-btn"),
                        cls="auth-container",
                    )
                ),
            )

        # Create new session
        session_id = str(uuid.uuid4())
        expires_at = datetime.now() + timedelta(days=7)

        cursor.execute(
            """
            INSERT INTO sessions (session_id, user_id, expires_at)
            VALUES (%s, %s, %s)
            """,
            (session_id, user[0], expires_at),
        )
        conn.commit()

        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=7 * 24 * 60 * 60,
            secure=True,
            samesite="lax",
        )
        return response

    except Exception as e:
        logging.error(f"Error in login: {str(e)}")
        conn.rollback()
        return Html(
            Head(Title("Login Error - Voice2Note"), Style(get_common_styles())),
            Body(
                Div(
                    H1("Login Error", cls="auth-title"),
                    P("An error occurred. Please try again.", cls="error-message"),
                    A("Try Again", href="/login", cls="auth-btn"),
                    cls="auth-container",
                )
            ),
        )


@rt("/api/logout", methods=["POST"])
async def api_logout(request):
    session_id = request.cookies.get("session_id")
    if session_id:
        cursor.execute(
            "UPDATE sessions SET deleted_at = CURRENT_TIMESTAMP WHERE session_id = %s",
            (session_id,),
        )
        conn.commit()

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="session_id")
    return response


# Middleware for auth checking
def get_current_user_id(request):
    session_id = request.cookies.get("session_id")
    if not session_id:
        return None

    cursor.execute(
        """
        SELECT user_id FROM sessions 
        WHERE session_id = %s 
        AND deleted_at IS NULL 
        AND expires_at > CURRENT_TIMESTAMP
        """,
        (session_id,),
    )
    result = cursor.fetchone()
    return result[0] if result else None


@rt("/")
def home(request):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
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
                    Form(
                        Button(
                            "Logout",
                            type="submit",
                            cls="logout-btn",
                        ),
                        method="POST",
                        action="/api/logout",
                    ),
                    style="position: absolute; top: 20px; right: 20px;",
                ),
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
                    .logout-btn {
                        padding: 8px 16px;
                        background-color: #dc3545;
                        color: white;
                        border: none;
                        border-radius: 4px;
                        cursor: pointer;
                        font-size: 14px;
                        transition: background-color 0.2s;
                    }
                    .logout-btn:hover {
                        background-color: #c82333;
                    }
                    """
                ),
                Script(
                    """
                    let recordingDuration = 0;
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
                            
                            audioPlayback.onloadedmetadata = () => {
                                window.audioBlob = file;
                                window.audioType = 'uploaded';
                                window.audioDuration = isFinite(audioPlayback.duration) ? audioPlayback.duration : 0;
                                document.getElementById('save').disabled = false;
                            };
                        }
                    });

                    document.getElementById('start').addEventListener('click', () => {
                    navigator.mediaDevices.getUserMedia({ audio: true })
                        .then(stream => {
                            mediaRecorder = new MediaRecorder(stream);
                            recordingDuration = 0;

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
                                
                                window.audioBlob = audioBlob;
                                window.audioType = 'recorded';
                                window.audioDuration = recordingDuration;
                                document.getElementById('save').disabled = false;
                            };

                            mediaRecorder.start();
                            document.getElementById('start').disabled = true;
                            document.getElementById('stop').disabled = false;

                            const timerElement = document.getElementById('recordTimer');
                            timerElement.style.display = 'block';
                            
                            recordInterval = setInterval(() => {
                                recordingDuration++;
                                const minutes = Math.floor(recordingDuration / 60);
                                const displaySeconds = recordingDuration % 60;
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
                    const duration = window.audioType === 'recorded' ? recordingDuration : (isFinite(window.audioDuration) ? window.audioDuration : 0);
                    
                    if (!audioBlob) {
                        alert('No audio to save!');
                        return;
                    }

                    // Convert duration to HH:MM:SS format
                    const hours = Math.floor(duration / 3600);
                    const minutes = Math.floor((duration % 3600) / 60);
                    const seconds = Math.floor(duration % 60);
                    const formattedDuration = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;

                    const formData = new FormData();
                    const timestamp = Math.floor(Date.now() / 1000);
                    const filename = `recording_${timestamp}.wav`;
                    formData.append('audio_file', audioBlob, filename);
                    formData.append('audio_type', audioType);
                    formData.append('duration', formattedDuration);

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
def notes(request, start_date: str = None, end_date: str = None, keyword: str = None):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)  # Base query
    query = """
        SELECT 
            audios.audio_key,
            TO_CHAR(audios.created_at, 'MM/DD') as note_date,
            COALESCE(transcription->>'note_title','Transcribing note...') as note_title,
            COALESCE(transcription->>'summary_text','Your audio is being transcribed. It will show up in here when is finished.') as note_summary,
            COALESCE(metadata->>'duration', '00:00:00') as duration
        FROM audios
        LEFT JOIN transcripts
        ON audios.audio_key = transcripts.audio_key
        WHERE user_id = %s
        AND audios.deleted_at IS NULL
    """
    query_params = [user_id]

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

    # Add keyword search if provided
    if keyword:
        query += " AND transcription->>'transcript_text' ILIKE %s"
        query_params.append(f"%{keyword}%")

    query += " ORDER BY audios.created_at DESC"

    cursor.execute(query, query_params)
    notes = cursor.fetchall()

    # Create search form with both date and keyword fields
    search_form = Div(
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
                Div(
                    Label("Search:", cls="keyword-label"),
                    Input(
                        type="text",
                        name="keyword",
                        cls="keyword-input",
                        value=keyword or "",
                        placeholder="Search in transcripts...",
                    ),
                    cls="keyword-field",
                ),
                Button("Search", type="submit", cls="search-btn"),
                Button(
                    "Clear", type="button", cls="clear-btn", onclick="clearSearch()"
                ),
                cls="search-container",
            ),
            method="GET",
            cls="search-form",
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
                Div(
                    P(
                        note[4] if note[4] else "0.00s",
                        cls="note-duration",
                    ),
                    Button(
                        I(cls="fas fa-trash"),
                        cls="delete-btn",
                        onclick=f"deleteNote('{note[0]}')",
                    ),
                    cls="note-actions",
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
            Link(
                rel="stylesheet",
                href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css",
            ),
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
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }
                .note-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: flex-start;
                    margin-bottom: 5px;
                    color: #333;
                }
                .note-actions {
                    display: flex;
                    align-items: flex-start;
                    gap: 10px;
                }
                .note-duration {
                    color: #666;
                    font-size: 0.9em;
                    margin: 0;
                    padding-top: 3px;
                    font-weight: bold;
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
                    font-weight: bold;
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
                
                /* Search form styles */
                .search-wrapper {
                    margin-bottom: 20px;
                    width: 100%;
                }
                .search-form {
                    width: 100%;
                }
                .search-container {
                    display: flex;
                    gap: 15px;
                    align-items: center;
                    justify-content: flex-end;
                    padding: 15px;
                    background-color: #f3f3f3;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    flex-wrap: wrap;
                }
                .date-field {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                }
                .date-label {
                    color: navy;
                    font-weight: 500;
                    white-space: nowrap;
                }
                .date-input {
                    padding: 8px;
                    border: 1px solid navy;
                    border-radius: 4px;
                    color: #333;
                }
                .keyword-field {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    flex-grow: 1;
                }
                .keyword-label {
                    color: navy;
                    font-weight: 500;
                    white-space: nowrap;
                }
                .keyword-input {
                    padding: 8px;
                    border: 1px solid navy;
                    border-radius: 4px;
                    color: #333;
                    width: 100%;
                    min-width: 200px;
                }
                .keyword-input::placeholder {
                    color: #999;
                }
                .search-btn {
                    padding: 8px 16px;
                    background-color: navy;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    white-space: nowrap;
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
                    white-space: nowrap;
                }
                .clear-btn:hover {
                    background-color: #555;
                }
                @media (max-width: 768px) {
                    .search-container {
                        flex-direction: column;
                        align-items: stretch;
                    }
                    .date-field, .keyword-field {
                        width: 100%;
                    }
                    .search-btn, .clear-btn {
                        width: 100%;
                    }
                }
                .delete-btn {
                    background: none;
                    border: none;
                    color: #dc3545;
                    cursor: pointer;
                    padding: 5px;
                    font-size: 1.1em;
                    opacity: 0.7;
                    transition: opacity 0.2s;
                    margin-top: -5px;
                }
                .delete-btn:hover {
                    opacity: 1;
                }
                .logout-btn {
                    padding: 8px 16px;
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: background-color 0.2s;
                }
                .logout-btn:hover {
                    background-color: #c82333;
                }
                """
            ),
            Script(
                """
                function clearSearch() {
                    document.querySelector('input[name="start_date"]').value = '';
                    document.querySelector('input[name="end_date"]').value = '';
                    document.querySelector('input[name="keyword"]').value = '';
                    window.location.href = '/notes';
                }

                function deleteNote(audioKey) {
                if (confirm('Are you sure you want to delete this note?')) {
                    fetch(`/delete-note/${audioKey}`, {
                        method: 'POST'
                    })
                    .then(response => {
                        if (response.ok) {
                            alert('Note deleted successfully!');
                            // In /notes endpoint
                            window.location.reload();
                            // In /note_{audio_key} endpoint
                            // window.location.href = '/notes';
                        } else {
                            alert('Failed to delete note.');
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Error deleting note.');
                    });
                }
            }
                """
            ),
        ),
        Body(
            Div(
                Form(
                    Button(
                        "Logout",
                        type="submit",
                        cls="logout-btn",
                    ),
                    method="POST",
                    action="/api/logout",
                ),
                style="position: absolute; top: 20px; right: 20px;",
            ),
            Div(
                A("\u2190 Back", href="/", cls="back-button"),
                Div(H1("Your Last Notes", cls="title")),
                Div(search_form, *note_cards, cls="container"),
            ),
        ),
    )


@rt("/note_{audio_key}")
def note_detail(request: Request, audio_key: str):
    # Get current user_id from session
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    cursor.execute(
        """
        SELECT 
            audios.audio_key,
            TO_CHAR(audios.created_at, 'MM/DD') as note_date,
            COALESCE(transcription->>'note_title','Transcribing note...') as note_title,
            COALESCE(transcription->>'transcript_text','Your audio is being transcribed. It will show up in here when is finished.') as note_transcription,
            metadata->>'duration' as duration
        FROM audios
        LEFT JOIN transcripts
        ON audios.audio_key = transcripts.audio_key
        WHERE audios.audio_key = %s
        AND audios.user_id = %s  -- Add user_id check
        AND audios.deleted_at IS NULL
        """,
        (audio_key, user_id),
    )
    note = cursor.fetchone()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return Html(
        Head(
            Title("Note Details - Voice2Note"),
            Link(
                rel="stylesheet",
                href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css",
            ),
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
                    align-items: flex-start;
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
                    font-weight: bold;
                }
                .note-transcription {
                    color: #333;
                    font-size: 16px;
                    line-height: 1.6;
                    white-space: pre-wrap;
                }
                .note-actions {
                    display: flex;
                    align-items: flex-start;
                    gap: 10px;
                }
                .note-duration {
                    color: #666;
                    font-size: 0.9em;
                    margin: 0;
                    padding-top: 3px;
                    font-weight: bold;
                }
                .delete-btn {
                    background: none;
                    border: none;
                    color: #dc3545;
                    cursor: pointer;
                    padding: 5px;
                    font-size: 1.1em;
                    opacity: 0.7;
                    transition: opacity 0.2s;
                    margin-top: -5px;
                }
                .delete-btn:hover {
                    opacity: 1;
                }
                .logout-btn {
                    padding: 8px 16px;
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: background-color 0.2s;
                }
                .logout-btn:hover {
                    background-color: #c82333;
                }
                """
            ),
            Script(
                """
                function deleteNote(audioKey) {
                    if (confirm('Are you sure you want to delete this note?')) {
                        fetch(`/delete-note/${audioKey}`, {
                            method: 'POST'
                        })
                        .then(response => {
                            if (response.ok) {
                                window.location.href = '/notes';
                            } else {
                                alert('Failed to delete note.');
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert('Error deleting note.');
                        });
                    }
                }
                """
            ),
        ),
        Body(
            Div(
                Form(
                    Button(
                        "Logout",
                        type="submit",
                        cls="logout-btn",
                    ),
                    method="POST",
                    action="/api/logout",
                ),
                style="position: absolute; top: 20px; right: 20px;",
            ),
            Div(
                A("\u2190 Back to Notes", href="/notes", cls="back-button"),
                Div(
                    Div(
                        P(note[1], cls="note-date"),
                        P(note[2], cls="note-title"),
                        cls="note-info",
                    ),
                    Div(
                        P(
                            note[4] if note[4] else "0.00s",
                            cls="note-duration",
                        ),
                        Button(
                            I(cls="fas fa-trash"),
                            cls="delete-btn",
                            onclick=f"deleteNote('{note[0]}')",
                        ),
                        cls="note-actions",
                    ),
                    cls="note-header",
                ),
                P(note[3], cls="note-transcription"),
                cls="container",
            ),
        ),
    )


@rt("/save-audio")
async def save_audio(
    request: Request,
    audio_file: UploadFile,
    audio_type: str = Form(...),
    duration: str = Form(...),
):
    # Get the current user_id from session
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        # Read file into memory for analysis
        contents = await audio_file.read()

        # Generate metadata with browser-provided duration
        metadata = {
            "duration": duration,
            "file_size": f"{len(contents) / 1024 / 1024:.2f}MB",
        }

        # Generate S3 file name
        timestamp = int(datetime.now().timestamp())
        prefix = "audios"
        s3_key = f"{prefix}/{user_id}_{timestamp}.wav"
        audio_key = f"{user_id}_{timestamp}"

        # Generate S3 URL
        s3_url = f"https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

        logging.info(f"Saving {audio_type} audio file with key: {audio_key}")

        # Insert record into PostgreSQL with audio_type
        try:
            cursor.execute(
                """
            INSERT INTO audios 
            (audio_key, user_id, s3_object_url, audio_type, created_at, metadata) 
            VALUES (%s, %s, %s, %s, %s, %s) 
            RETURNING audio_key
            """,
                (
                    audio_key,
                    user_id,
                    s3_url,
                    audio_type,
                    datetime.now(),
                    json.dumps(metadata),
                ),
            )
            conn.commit()
            logging.info(f"Database record created for audio_key: {audio_key}")
        except Exception as e:
            logging.error(
                f"Database insertion failed for audio_key {audio_key}: {str(e)}"
            )
            raise

        # Reset file pointer for S3 upload
        audio_file.file.seek(0)

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


@rt("/delete-note/{audio_key}")
async def delete_note(request: Request, audio_key: str):
    # Get current user_id from session
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # First verify the note belongs to the user
        cursor.execute(
            """
            SELECT user_id FROM audios 
            WHERE audio_key = %s AND deleted_at IS NULL
            """,
            (audio_key,),
        )
        note = cursor.fetchone()

        if not note:
            raise HTTPException(status_code=404, detail="Note not found")

        if note[0] != user_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to delete this note"
            )

        # Update both tables with current timestamp
        cursor.execute(
            """
            WITH audio_update AS (
                UPDATE audios 
                SET deleted_at = CURRENT_TIMESTAMP 
                WHERE audio_key = %s
                AND user_id = %s  -- Add user_id check
            )
            UPDATE transcripts 
            SET deleted_at = CURRENT_TIMESTAMP 
            WHERE audio_key = %s;
            """,
            (audio_key, user_id, audio_key),
        )
        conn.commit()
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting note: {str(e)}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Error deleting note")


serve()
