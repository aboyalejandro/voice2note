from fasthtml.common import *
from datetime import datetime, timedelta
import logging
import json
import bcrypt
import uuid
import io
from starlette.responses import StreamingResponse
from queries import (
    create_user_schema,
    validate_schema,
    get_notes,
    get_note_detail,
)
from styles import get_common_styles
from config import conn, s3, logger, AWS_S3_BUCKET
from llm import (
    get_chat_completion,
    find_relevant_context,
    generate_chat_title,
    RateLimiter,
)


# Limiter for LLM
rate_limiter = RateLimiter()

# Setup PostgreSQL
cursor = conn.cursor()

# Initialize FastHTML app
app, rt = fast_app()


@rt("/login")
def login(request: Request):
    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
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
                    " • ",
                    A("Forgot Password?", href="/forgot-password"),
                    cls="auth-link",
                ),
            ),
        ),
    )


@rt("/signup")
def signup(request: Request):
    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
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


@rt("/api/signup", methods=["POST"])
async def api_signup(request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    logger.info(f"Processing signup request for username: {username}")

    # Check if username already exists
    cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
    if cursor.fetchone():
        logger.warning(f"Signup failed - username already exists: {username}")
        return Html(
            Head(
                Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
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

    try:
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

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
        logger.info(f"User created successfully - user_id: {user_id}")

        # Create user schema and tables
        create_user_schema(user_id)
        logger.info(f"User schema created successfully - user_id: {user_id}")

        # Create session
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
        logger.info(
            f"Session created successfully - user_id: {user_id}, session_id: {session_id}"
        )

        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=7 * 24 * 60 * 60,
            secure=True,
            samesite="lax",
        )
        response.set_cookie(
            key="schema",
            value=f"{user_id}",
            httponly=True,
            max_age=7 * 24 * 60 * 60,
            secure=True,
            samesite="lax",
        )
        return response

    except Exception as e:
        conn.rollback()
        logger.error(f"Error in signup process: {str(e)}", exc_info=True)
        logging.error(f"Error in signup: {str(e)}")
        return Html(
            Head(
                Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
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
    logger.info(f"Found user {username} in database.")

    if not user:
        return Html(
            Head(
                Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
                Title("Login Error - Voice2Note"),
                Style(get_common_styles()),
            ),
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
                Head(
                    Meta(
                        name="viewport", content="width=device-width, initial-scale=1.0"
                    ),
                    Title("Login Error - Voice2Note"),
                    Style(get_common_styles()),
                ),
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
        logger.info(f"Created new session: {session_id}.")

        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=7 * 24 * 60 * 60,
            secure=True,
            samesite="lax",
        )
        response.set_cookie(
            key="schema",
            value=f"user_{user[0]}",
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
            Head(
                Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
                Title("Login Error - Voice2Note"),
                Style(get_common_styles()),
            ),
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
        logger.info(f"Finished session: {session_id}.")

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key="session_id")
    return response


@rt("/forgot-password")
def forgot_password():
    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Reset Password - Voice2Note"),
            Style(get_common_styles()),
        ),
        Body(
            Div(
                H1("Reset Password", cls="auth-title"),
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
                    Button("Request Reset", type="submit", cls="auth-btn"),
                    method="POST",
                    action="/api/request-reset",
                    cls="auth-form",
                ),
                P(
                    "Remember your password? ",
                    A("Login", href="/login"),
                    cls="auth-link",
                ),
                cls="auth-container",
            )
        ),
    )


@rt("/reset-password/{token}")
def reset_password(token: str):
    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Set New Password - Voice2Note"),
            Style(get_common_styles()),
        ),
        Body(
            Div(
                H1("Set New Password", cls="auth-title"),
                Form(
                    Div(
                        Label("New Password", For="password", cls="form-label"),
                        Input(
                            type="password",
                            name="password",
                            id="password",
                            required=True,
                            cls="form-input",
                            placeholder="Enter new password",
                        ),
                        cls="form-group",
                    ),
                    Input(type="hidden", name="token", value=token),
                    Button("Reset Password", type="submit", cls="auth-btn"),
                    method="POST",
                    action="/api/reset-password",
                    cls="auth-form",
                ),
                cls="auth-container",
            )
        ),
    )


@rt("/api/request-reset", methods=["POST"])
async def request_reset(request):
    form = await request.form()
    username = form.get("username")

    # Check if user exists
    cursor.execute("SELECT user_id FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    logger.info(f"Validating password reset request for user_id {user}...")

    if not user:
        return Html(
            Head(
                Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
                Title("Reset Password Error"),
                Style(get_common_styles()),
            ),
            Body(
                Div(
                    H1("Reset Password Error", cls="auth-title"),
                    P("Username not found", cls="error-message"),
                    A("Try Again", href="/forgot-password", cls="auth-btn"),
                    cls="auth-container",
                )
            ),
        )

    # Generate reset token and set expiration
    reset_token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(hours=1)

    # Save token to database
    cursor.execute(
        """
        UPDATE users 
        SET reset_token = %s, reset_token_expires = %s 
        WHERE username = %s
        """,
        (reset_token, expires_at, username),
    )
    conn.commit()
    logger.info(f"Saved password reset token for user_id {user}...")

    # Pending email recovery
    reset_link = f"/reset-password/{reset_token}"

    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Reset Password"),
            Style(get_common_styles()),
        ),
        Body(
            Div(
                H1("Reset Password", cls="auth-title"),
                P("Password reset link generated:", cls="info-message"),
                A(
                    "Click here to reset password",
                    href=reset_link,
                    cls="auth-btn",
                    style="display: block; text-align: center; margin: 20px 0;",
                ),
                P(
                    "This link will expire in 1 hour.",
                    style="text-align: center; color: #666;",
                ),
                cls="auth-container",
            )
        ),
    )


@rt("/api/reset-password", methods=["POST"])
async def reset_password_submit(request):
    form = await request.form()
    token = form.get("token")
    new_password = form.get("password")

    # Verify token and get user
    cursor.execute(
        """
        SELECT user_id 
        FROM users 
        WHERE reset_token = %s 
        AND reset_token_expires > CURRENT_TIMESTAMP
        """,
        (token,),
    )
    user = cursor.fetchone()
    logger.info(f"Validating password reset token for user_id {user}...")

    if not user:
        return Html(
            Head(
                Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
                Title("Reset Error"),
                Style(get_common_styles()),
            ),
            Body(
                Div(
                    H1("Reset Error", cls="auth-title"),
                    P("Invalid or expired reset link", cls="error-message"),
                    A("Back to Login", href="/login", cls="auth-btn"),
                    cls="auth-container",
                )
            ),
        )

    # Update password and clear reset token
    hashed_password = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt())
    cursor.execute(
        """
        UPDATE users 
        SET hashed_password = %s, reset_token = NULL, reset_token_expires = NULL 
        WHERE user_id = %s
        """,
        (hashed_password.decode("utf-8"), user[0]),
    )
    conn.commit()
    logger.info(f"Password token for {user} has been completed.")

    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Password Reset Success"),
            Style(get_common_styles()),
        ),
        Body(
            Div(
                H1("Password Reset Success", cls="auth-title"),
                P(
                    "Your password has been successfully reset.",
                    style="text-align: center; margin: 20px 0;",
                ),
                A("Login Now", href="/login", cls="auth-btn"),
                cls="auth-container",
            )
        ),
    )


@rt("/")
def home(request):
    schema = validate_schema(request.cookies.get("schema"))
    if not schema:
        return RedirectResponse(url="/login", status_code=303)
    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Voice2Note"),
        ),
        Body(
            Div(
                "Voice2Note",
                style="color: navy; font-size: 2rem; font-weight: bold; text-align: center;",
            ),
            Div(
                P(
                    "Record, upload, find and edit your transcribed notes effortlessly.",
                    P(
                        "Only supports EN and ES audios.",
                        style="margin-top: 5px;",
                    ),
                    style="color: navy; font-size: 1rem; text-align: center;",
                ),
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
                        accept="audio/wav,audio/mp3,audio/webm",
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
                    Button(
                        I(cls="fas fa-robot"),  # Added chat robot icon
                        id="chat",
                        cls="chat-btn",
                        title="Chat with Notes",
                        onclick="startNewChat()",
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
                        "⚠️ Only ",
                        B(".mp3"),
                        ", ",
                        B(".wav"),
                        " and ",
                        B(".webm"),
                        " can be uploaded. You can play the audio before saving it.",
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
                    .chat-btn {
                        font-size: 40px;
                        background: none;
                        border: none;
                        cursor: pointer;
                        padding: 10px;
                        margin: 0 10px;
                        color: navy;
                    }
                    .chat-btn:hover {
                        color: #2196F3;
                    }
                    """
                ),
                Script(
                    """
                    let mediaRecorder;
                    let audioChunks = [];
                    let recordingDuration = 0;
                    let recordInterval;

                    document.getElementById('upload').addEventListener('click', () => {
                        document.getElementById('uploadInput').click();
                    });

                    document.getElementById('uploadInput').addEventListener('change', async (event) => {
                        const file = event.target.files[0];
                        const saveButton = document.getElementById('save');

                        if (file) {
                            const allowedExtensions = ['wav', 'mp3', 'webm'];
                            const fileExtension = file.name.split('.').pop().toLowerCase();

                            console.log('Detected MIME type:', file.type); // Debug MIME type
                            console.log('Detected file extension:', fileExtension); // Debug extension

                            if (!allowedExtensions.includes(fileExtension)) {
                                alert(`Invalid file type (${fileExtension}). Please upload a .wav, .mp3, or .webm file.`);
                                event.target.value = ''; // Clear the input
                                return;
                            }

                            const audioUrl = URL.createObjectURL(file);
                            const audioPlayback = document.getElementById('audioPlayback');
                            audioPlayback.src = audioUrl;

                            window.audioBlob = file;
                            window.audioType = 'uploaded';
                            saveButton.disabled = false;
                        }
                    });

                    document.getElementById('stop').addEventListener('click', () => {
                        if (mediaRecorder && mediaRecorder.state === 'recording') {
                            mediaRecorder.stop();
                            document.getElementById('start').disabled = false;
                            document.getElementById('stop').disabled = true;
                            mediaRecorder.stream.getTracks().forEach(track => track.stop());
                        }
                    });

                    document.getElementById('start').addEventListener('click', () => {
                        navigator.mediaDevices.getUserMedia({ audio: true })
                            .then(stream => {
                                const options = {
                                    mimeType: 'audio/webm;codecs=opus',
                                    audioBitsPerSecond: 128000
                                };
                                
                                mediaRecorder = new MediaRecorder(stream, options);
                                recordingDuration = 0;
                                audioChunks = [];
                                
                                mediaRecorder.ondataavailable = event => {
                                    audioChunks.push(event.data);
                                };

                                mediaRecorder.onstop = () => {
                                    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                                    const audioUrl = URL.createObjectURL(audioBlob);
                                    const audioPlayback = document.getElementById('audioPlayback');
                                    audioPlayback.src = audioUrl;
                                    
                                    clearInterval(recordInterval);
                                    document.getElementById('recordTimer').style.display = 'none';
                                    
                                    window.audioBlob = audioBlob;
                                    window.audioType = 'recorded';
                                    document.getElementById('save').disabled = false;
                                };

                                mediaRecorder.start(1000);
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
                            })
                            .catch(error => {
                                console.error('Error accessing microphone:', error);
                                alert('Error accessing microphone. Please ensure you have given permission.');
                            });
                    });

                    document.getElementById('save').addEventListener('click', () => {
                        const audioBlob = window.audioBlob;
                        const audioType = window.audioType;
                        const saveButton = document.getElementById('save');

                        if (!audioBlob) {
                            alert('No audio to save!');
                            return;
                        }

                        const formData = new FormData();
                        const timestamp = Math.floor(Date.now() / 1000);
                        const extension = audioBlob.type.split('/')[1]; // Extract file extension
                        const filename = `recording_${timestamp}.${extension}`;

                        formData.append('audio_file', audioBlob, filename);
                        formData.append('audio_type', audioType);

                        saveButton.textContent = 'Saving...';
                        saveButton.disabled = true;

                        fetch('/save-audio', {
                            method: 'POST',
                            body: formData,
                        })
                            .then(response => {
                                if (!response.ok) {
                                    return response.text().then(text => {
                                        throw new Error(`Failed to save audio: ${text}`);
                                    });
                                }
                                return response.json();
                            })
                            .then(data => {
                                alert('Audio saved successfully!');
                                window.audioBlob = null;
                                document.getElementById('audioPlayback').src = '';
                            })
                            .catch(error => {
                                alert(error.message || 'Failed to save audio. Please try again.');
                            })
                            .finally(() => {
                                saveButton.textContent = 'Save Audio';
                                saveButton.disabled = false;
                            });
                    });

                    function startNewChat() {
                        const sessionId = Math.random().toString(36).substring(7);
                        window.location.href = `/chat_${sessionId}`;
                    }
            """
                ),
            ),
        ),
    )


@rt("/notes")
def notes(request, start_date: str = None, end_date: str = None, keyword: str = None):
    schema = validate_schema(request.cookies.get("schema"))
    if not schema:
        return RedirectResponse(url="/login", status_code=303)

    # Build query based on filters
    query = get_notes(schema)
    query_params = []

    # Add date filtering if dates are provided
    if start_date or end_date:
        query += " WHERE DATE(sort_date)"
        if start_date and end_date:
            query += " BETWEEN %s AND %s"
            query_params.extend([start_date, end_date])
        elif start_date:
            query += " >= %s"
            query_params.append(start_date)
        elif end_date:
            query += " <= %s"
            query_params.append(end_date)

    # Add keyword search if provided
    if keyword:
        keyword_condition = f"""
        {' WHERE ' if not (start_date or end_date) else ' AND '}(
            title ILIKE %s 
            OR preview ILIKE %s
            OR content_id IN (
                SELECT chat_id 
                FROM {schema}.chat_messages 
                WHERE content ILIKE %s
            )
        )"""
        query += keyword_condition
        query_params.extend([f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"])

    query += " ORDER BY sort_date DESC"

    # Execute query in user's schema
    cursor.execute(query, query_params)
    items = cursor.fetchall()
    conn.commit()

    # Create search form with both date and keyword fields
    search_form = Div(
        Form(
            Div(
                Div(
                    I(cls="fas fa-calendar", style="color: navy;"),
                    "From: ",
                    Input(
                        type="date",
                        name="start_date",
                        cls="date-input",
                        value=start_date or "",
                        title="From date",
                    ),
                    "To: ",
                    Input(
                        type="date",
                        name="end_date",
                        cls="date-input",
                        value=end_date or "",
                        title="To date",
                    ),
                    cls="date-field",
                ),
                Div(
                    Input(
                        type="text",
                        name="keyword",
                        cls="keyword-input",
                        value=keyword or "",
                        placeholder="Search in notes...",
                    ),
                    cls="keyword-field",
                ),
                Div(
                    Button(I(cls="fas fa-search"), type="submit", cls="search-btn"),
                    Button(
                        I(cls="fas fa-times"),
                        type="button",
                        cls="clear-btn",
                        onclick="clearSearch()",
                    ),
                    cls="button-field",
                ),
                cls="search-container",
            ),
            method="GET",
            cls="search-form",
        ),
        cls="search-wrapper",
    )

    content_cards = [
        Div(
            Div(
                Div(
                    P(item[2], cls="note-date"),  # created_date
                    P(item[3], cls="note-title"),  # title
                    cls="note-info",
                ),
                Div(
                    # For chats, show robot icon
                    (
                        I(cls="fas fa-robot", style="color: #2196F3; font-size: 1.2em;")
                        if item[0] == "chat"
                        else None
                    ),
                    P(
                        item[5],  # duration or message count
                        cls=(
                            "note-duration"
                            if item[0] == "note"
                            else "chat-message-count"
                        ),
                    ),
                    cls="note-actions",
                ),
                cls="note-header",
            ),
            P(item[4], cls="note-preview"),  # preview
            Div(
                A(
                    Button("View", cls="view-btn"),
                    href=f"/{'note' if item[0] == 'note' else 'chat'}_{item[1]}",
                ),
                style="text-align: right; margin-top: 10px;",
            ),
            cls=f"{'note' if item[0] == 'note' else 'chat'}",
        )
        for item in items
    ]

    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
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
                    margin: 40px 0 20px 20px; /* Added left margin */
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
                    margin-left: 10px; 
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
                    align-items: center;  /* Center align all items vertically */
                    margin-bottom: 5px;
                    color: #333;
                }
                .note-info {
                    display: flex;
                    align-items: center;  /* Center align date and title vertically */
                    gap: 10px;
                    flex: 1;
                }
                .note-title {
                    color: navy;
                    font-weight: bold;
                    font-size: clamp(0.9em, 2vw, 1.2em);
                    margin: 0;
                    word-break: break-word;
                    line-height: 1.3;
                    display: flex;
                    align-items: center;  /* Center text vertically */
                }
                .note-duration {
                    color: #666;
                    font-size: 0.9em;
                    margin: 0;
                    font-weight: bold;
                    display: inline-flex;
                    align-items: center;
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
                    display: -webkit-box;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    -webkit-line-clamp: 3; /* Show 3 lines max */
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
                
                //* Search form styles */
                .search-wrapper {
                    margin-bottom: 20px;
                    width: 100%;
                }
                .search-form {
                    width: 100%;
                }
                /* Search container responsive adjustments */
                .search-container {
                    display: flex;
                    gap: 10px;
                    align-items: center;
                    padding: 12px;
                    background-color: #f3f3f3;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }

                .date-field {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    flex: 1;  /* Allow date field to grow */
                }

                .keyword-field {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    flex: 2;  /* Give keyword field more growing space */
                }

                .keyword-input {
                    padding: 6px 12px;
                    border: 1px solid navy;
                    border-radius: 4px;
                    color: #333;
                    width: 100%;
                    font-size: 14px;
                }

                .keyword-input::placeholder {
                    color: #999;
                }

                .date-input {
                    padding: 6px;
                    border: 1px solid navy;
                    border-radius: 4px;
                    color: #333;
                    width: 130px;
                    font-size: 14px;
                    flex: 1;  /* Allow inputs to grow within date-field */
                    min-width: 110px;  /* Minimum width to prevent too much shrinking */
                }

                .date-input::-webkit-calendar-picker-indicator {
                    cursor: pointer;
                }

                .button-field {
                    display: flex;
                    gap: 6px;
                }
                .search-btn, .clear-btn {
                    padding: 6px 12px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 16px;
                }
                .search-btn {
                    background-color: navy;
                    color: white;
                }
                .search-btn:hover {
                    background-color: #004080;
                }
                .clear-btn {
                    background-color: #666;
                    color: white;
                }
                .clear-btn:hover {
                    background-color: #555;
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

                @media (max-width: 768px) {
                    .search-container {
                        flex-direction: column;
                        align-items: stretch;
                    }
                    
                    .date-field, .keyword-field {
                        width: 100%;
                    }
                    
                    .date-field {
                        justify-content: space-between;
                        flex-wrap: wrap;
                        gap: 10px;
                    }
                    
                    .note-preview {
                        -webkit-line-clamp: 2; /* Show 2 lines on mobile */
                    }
                }

                @media (max-width: 400px) {
                    .date-input {
                        min-width: 90px;  /* Even smaller minimum width for very small screens */
                    }
                    
                    .date-field span {
                        min-width: 35px;
                    }
                }

                /* Search container and button styles */
                .search-container {
                    display: flex;
                    gap: 10px;
                    align-items: center;
                    padding: 12px;
                    background-color: #f3f3f3;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                }

                .button-field {
                    display: flex;
                    gap: 6px;
                }

                .search-btn, .clear-btn {
                    padding: 6px 12px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 16px;
                }

                .search-btn {
                    background-color: navy;
                    color: white;
                }

                .clear-btn {
                    background-color: #666;
                    color: white;
                }

                /* Responsive adjustments */
                @media (max-width: 755px) {
                    .search-container {
                        flex-direction: column;
                        align-items: stretch;
                    }
                    
                    .date-field, .keyword-field {
                        width: 100%;
                    }
                    
                    .button-field {
                        display: flex;
                        gap: 10px;
                        width: 100%;
                    }
                    
                    .search-btn, .clear-btn {
                        flex: 1;  /* Make buttons expand equally */
                        padding: 10px;  /* Slightly larger padding for better touch targets */
                    }
                }
                .chat {
                    display: flex;
                    flex-direction: column;
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 15px;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                    border-left: 3px solid #2196F3;
                }

                .chat .note-title {
                    color: #2196F3;
                    font-size: clamp(0.9em, 2vw, 1.2em);
                    margin: 0;
                    word-break: break-word;
                    line-height: 1.3;
                }

                .chat-message-count {
                    color: #666;
                    font-size: 0.9em;
                    margin: 0;
                    font-weight: bold;
                    display: inline-flex;
                    align-items: center;
                    gap: 5px;
                }

                .chat .note-preview {
                    color: #555;
                    font-size: 14px;
                    display: -webkit-box;
                    -webkit-box-orient: vertical;
                    overflow: hidden;
                    text-overflow: ellipsis;
                    -webkit-line-clamp: 2;
                    font-style: italic;
                }

                .fa-robot {
                    color: #2196F3;
                    font-size: 1.2em;
                    margin-right: 8px;
                }

                /* Responsive adjustments */
                @media (max-width: 768px) {
                    .chat {
                        padding: 12px;
                    }

                    .chat .note-header {
                        flex-direction: row;
                        justify-content: space-between;
                        align-items: center;
                    }

                    .chat-message-count {
                        font-size: 0.85em;
                    }

                    .chat .note-preview {
                        font-size: 13px;
                        -webkit-line-clamp: 2;
                    }
                }

                @media (max-width: 480px) {
                    .chat {
                        padding: 10px;
                    }

                    .chat .note-title {
                        font-size: 0.95em;
                    }

                    .chat-message-count {
                        font-size: 0.8em;
                    }

                    .fa-robot {
                        font-size: 1.1em;
                        margin-right: 6px;
                    }
                }

                /* Landscape mode adjustments */
                @media (max-height: 600px) and (orientation: landscape) {
                    .chat {
                        margin-bottom: 10px;
                    }
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
                A("\u2190", href="/", cls="back-button"),
                Div(H1("Your Last Notes", cls="title")),
                Div(
                    search_form,
                    *(
                        content_cards
                        if content_cards
                        else "Your notes and chats will show up here when you record or upload them."
                    ),
                    cls="container",
                ),
            ),
        ),
    )


@rt("/note_{audio_key}")
def note_detail(request: Request, audio_key: str):
    # Get current user_id from session
    schema = validate_schema(request.cookies.get("schema"))
    if not schema:
        return RedirectResponse(url="/login", status_code=303)

    # Query note details in user's schema
    cursor.execute(
        get_note_detail(schema),
        (audio_key,),
    )
    note = cursor.fetchone()

    # Handle note not found
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
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

                .delete-btn {
                    background: none;
                    border: none;
                    color: #dc3545;
                    cursor: pointer;
                    padding: 5px;
                    font-size: 1.1em;
                    opacity: 0.7;
                    transition: opacity 0.2s;
                    margin: 0;
                    display: inline-flex;
                    align-items: center;
                }
                .delete-btn:hover {
                    opacity: 1;
                }
                .edit-btn {
                    background: none;
                    border: none;
                    color: #2196F3;
                    cursor: pointer;
                    padding: 5px;
                    font-size: 1.1em;
                    opacity: 0.7;
                    transition: opacity 0.2s;
                    margin-top: -5px;
                }
                .edit-btn:hover {
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
                .edit-container {
                    margin-top: 20px;
                    width: 100%;
                }
                .edit-title {
                    color: navy;
                    font-size: 1.5em;
                    margin-bottom: 20px;
                }
                .edit-form {
                    width: 100%;
                    background-color: white;
                    border-radius: 8px;
                }
                .form-input {
                    width: 100%;
                    padding: 12px;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    font-size: 1.2em;
                    color: navy;
                    margin-bottom: 15px;
                }
                .form-textarea {
                    width: 100%;
                    min-height: 300px;
                    padding: 12px;
                    border: 1px solid #e0e0e0;
                    border-radius: 4px;
                    font-size: 16px;
                    line-height: 1.6;
                    resize: vertical;
                    color: #333;
                    margin-bottom: 15px;
                }
                .form-buttons {
                    display: flex;
                    gap: 10px;
                    justify-content: flex-end;
                }
                .save-btn, .cancel-btn {
                    padding: 10px 20px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                    transition: background-color 0.2s;
                }
                .save-btn {
                    background-color: #28a745;
                    color: white;
                }
                .save-btn:hover {
                    background-color: #218838;
                }
                .cancel-btn {
                    background-color: #6c757d;
                    color: white;
                }
                .cancel-btn:hover {
                    background-color: #5a6268;
                }
                .note-container, .edit-container {
                    transition: opacity 0.3s ease;
                }
                .play-btn {
                    background: none;
                    border: none;
                    color: #4CAF50;
                    cursor: pointer;
                    padding: 5px;
                    font-size: 1.1em;
                    opacity: 0.7;
                    transition: opacity 0.2s;
                    margin-top: -5px;
                }
                .play-btn:hover {
                    opacity: 1;
                }
                .audio-player {
                    width: 100%;
                    max-width: 300px;
                    margin-right: 10px;
                }

                .play-btn,
                .edit-btn,
                .delete-btn {
                    font-size: 1.2em;
                    padding: 8px;
                }
            """
            ),
            Script(
                """
                function toggleEditMode(show) {
                    const editContainer = document.querySelector('.edit-container');
                    const noteContainer = document.querySelector('.note-container');
                    
                    if (show) {
                        noteContainer.style.display = 'none';
                        editContainer.style.display = 'block';
                        // Focus on title input
                        setTimeout(() => {
                            document.getElementById('edit-title').focus();
                        }, 50);
                    } else {
                        editContainer.style.display = 'none';
                        noteContainer.style.display = 'block';
                    }
                }

                async function saveNote(audioKey) {
                    const title = document.getElementById('edit-title').value;
                    const transcript = document.getElementById('edit-transcript').value;

                    if (!title.trim() || !transcript.trim()) {
                        alert('Title and transcript cannot be empty');
                        return;
                    }

                    try {
                        const response = await fetch(`/edit-note/${audioKey}`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                note_title: title,
                                transcript_text: transcript
                            })
                        });

                        if (response.ok) {
                            // Update the displayed content
                            document.querySelector('.note-title').textContent = title;
                            document.querySelector('.note-transcription').textContent = transcript;
                            toggleEditMode(false);
                        } else {
                            alert('Failed to save changes.');
                        }
                    } catch (error) {
                        console.error('Error:', error);
                        alert('Error saving changes.');
                    }
                }

                // Add keyboard shortcuts
                document.addEventListener('keydown', function(e) {
                    const editContainer = document.querySelector('.edit-container');
                    if (editContainer.style.display === 'block') {
                        // Escape to cancel
                        if (e.key === 'Escape') {
                            toggleEditMode(false);
                        }
                        // Ctrl/Cmd + Enter to save
                        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                            const audioKey = window.location.pathname.split('_')[1];
                            saveNote(audioKey);
                        }
                    }
                });

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
                
                let audioPlayer = null;
                let isPlaying = false;

                async function toggleAudio(audioKey) {
                    const playBtn = document.getElementById('play-btn');
                    const durationDisplay = document.getElementById('duration-display');
                    let audioPlayer = document.getElementById('audio-player');

                    if (!isPlaying) {
                        try {
                            playBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                            
                            // Fetch the audio file
                            const response = await fetch(`/get-audio/${audioKey}`);
                            if (!response.ok) throw new Error('Failed to fetch audio');
                            
                            const blob = await response.blob();
                            const audioUrl = URL.createObjectURL(blob);
                            
                            // Create a new audio element if it doesn't exist
                            if (!audioPlayer) {
                                audioPlayer = document.createElement('audio');
                                audioPlayer.id = 'audio-player';
                                audioPlayer.className = 'audio-player';
                                // Insert after the play button
                                playBtn.parentNode.insertBefore(audioPlayer, playBtn.nextSibling);
                            }
                            
                            // Set source and try to play
                            audioPlayer.src = audioUrl;
                            audioPlayer.style.display = 'block';
                            if (durationDisplay) {
                                durationDisplay.style.display = 'none';
                            }
                            
                            // Add error handler
                            audioPlayer.onerror = (e) => {
                                console.error('Audio playback error:', e);
                                alert('This audio format might not be supported by your browser.');
                                playBtn.innerHTML = '<i class="fas fa-play"></i>';
                                isPlaying = false;
                            };
                            
                            // Try playing
                            const playPromise = audioPlayer.play();
                            if (playPromise !== undefined) {
                                playPromise
                                    .then(() => {
                                        playBtn.innerHTML = '<i class="fas fa-pause"></i>';
                                        isPlaying = true;
                                    })
                                    .catch(error => {
                                        console.error('Playback failed:', error);
                                        playBtn.innerHTML = '<i class="fas fa-play"></i>';
                                        isPlaying = false;
                                    });
                            }
                            
                            // Handle audio end
                            audioPlayer.onended = () => {
                                playBtn.innerHTML = '<i class="fas fa-play"></i>';
                                audioPlayer.style.display = 'none';
                                if (durationDisplay) {
                                    durationDisplay.style.display = 'block';
                                }
                                isPlaying = false;
                            };
                        } catch (error) {
                            console.error('Error playing audio:', error);
                            alert('Failed to play audio.');
                            playBtn.innerHTML = '<i class="fas fa-play"></i>';
                            isPlaying = false;
                        }
                    } else {
                        // Pause audio
                        if (audioPlayer) {
                            audioPlayer.pause();
                            playBtn.innerHTML = '<i class="fas fa-play"></i>';
                            audioPlayer.style.display = 'none';
                            if (durationDisplay) {
                                durationDisplay.style.display = 'block';
                            }
                            isPlaying = false;
                        }
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
                A("\u2190", href="/notes", cls="back-button"),
                # Note display container
                Div(
                    Div(
                        Div(
                            P(note[1], cls="note-date"),
                            P(note[2], cls="note-title"),
                            cls="note-info",
                        ),
                        Div(
                            Button(
                                I(cls="fas fa-play"),
                                cls="play-btn",
                                id="play-btn",
                                onclick=f"toggleAudio('{note[0]}')",
                            ),
                            Button(
                                I(cls="fas fa-edit"),
                                cls="edit-btn",
                                onclick="toggleEditMode(true)",
                            ),
                            Button(
                                I(cls="fas fa-trash"),
                                cls="delete-btn",
                                onclick=f"deleteNote('{note[0]}')",
                            ),
                            cls="note-actions",
                        ),
                        cls="note-header note-detail",
                    ),
                    P(note[3], cls="note-transcription"),
                    cls="note-container",
                ),
                # Edit form container
                Div(
                    Form(
                        Input(
                            type="text",
                            id="edit-title",
                            name="title",
                            value=note[2],
                            cls="form-input",
                            placeholder="Enter title",
                        ),
                        Textarea(
                            note[3],
                            id="edit-transcript",
                            name="transcript",
                            cls="form-textarea",
                            placeholder="Enter transcript",
                        ),
                        Div(
                            Button(
                                "Save",
                                type="button",
                                onclick=f"saveNote('{note[0]}')",
                                cls="save-btn",
                            ),
                            Button(
                                "Cancel",
                                type="button",
                                onclick="toggleEditMode(false)",
                                cls="cancel-btn",
                            ),
                            cls="form-buttons",
                        ),
                        cls="edit-form",
                    ),
                    cls="edit-container",
                    style="display: none;",
                ),
                cls="container",
            ),
        ),
    )


@rt("/save-audio")
async def save_audio(
    request: Request,
    audio_file: UploadFile,
    audio_type: str = Form(...),
):
    schema = validate_schema(request.cookies.get("schema"))
    if not schema:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Determine the file extension
        mime_type = audio_file.content_type
        file_extension = audio_file.filename.split(".")[-1].lower()

        # Map MIME types to correct file extensions
        mime_to_extension = {
            "audio/mpeg": "mp3",
            "audio/wav": "wav",
            "audio/webm": "webm",
        }

        if mime_type in mime_to_extension:
            file_extension = mime_to_extension[mime_type]

        # Generate keys and paths
        timestamp = int(datetime.now().timestamp())
        audio_key = f"{schema}_{timestamp}"
        s3_key = f"user_{schema}/audios/raw/{audio_key}.{file_extension}"
        s3_url = f"s3://{AWS_S3_BUCKET}/{s3_key}"

        logging.info(f"Saving {audio_type} audio file with key: {audio_key}")

        # Insert record using user schema
        query = f"""
            INSERT INTO {schema}.audios (audio_key, user_id, s3_object_url, audio_type, created_at)
            VALUES (%s, %s, %s, %s, %s) 
            RETURNING audio_key
        """
        query_params = [
            audio_key,
            schema,
            s3_url,
            audio_type,
            datetime.now(),
        ]

        cursor.execute(query, query_params)
        conn.commit()
        logging.info(f"Database record created for audio_key: {audio_key}")

        # Upload to S3
        s3.upload_fileobj(audio_file.file, AWS_S3_BUCKET, s3_key)
        logging.info(f"Audio file uploaded to S3: {s3_key}")

        return {"audio_key": audio_key}

    except Exception as e:
        logging.error(f"Error saving audio: {str(e)}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Error saving audio")


@rt("/delete-note/{audio_key}")
async def delete_note(request: Request, audio_key: str):
    schema = validate_schema(request.cookies.get("schema"))
    if not schema:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Check if note exists
        cursor.execute(
            f"SELECT 1 FROM {schema}.audios WHERE audio_key = %s AND deleted_at IS NULL",
            (audio_key,),
        )

        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Note not found")

        # Soft delete
        cursor.execute(
            f"""
            WITH audio_update AS (
                UPDATE {schema}.audios 
                SET deleted_at = CURRENT_TIMESTAMP 
                WHERE audio_key = %s
            )
            UPDATE {schema}.transcripts 
            SET deleted_at = CURRENT_TIMESTAMP 
            WHERE audio_key = %s
            """,
            (audio_key, audio_key),
        )
        conn.commit()
        logger.info(f"Removed audio and transcript for audio_key {audio_key}.")

        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting note: {str(e)}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Error deleting note")


@rt("/edit-note/{audio_key}", methods=["POST"])
async def edit_note(request: Request, audio_key: str):
    schema = validate_schema(request.cookies.get("schema"))
    if not schema:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Get the updated content from request body
        body = await request.json()
        note_title = body.get("note_title")
        transcript_text = body.get("transcript_text")
        current_timestamp = datetime.now().isoformat()

        # Verify note exists and belongs to user
        cursor.execute(
            f"SELECT transcription FROM {schema}.transcripts WHERE audio_key = %s",
            (audio_key,),
        )
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="Note not found")

        # Get existing transcription or create new one
        current_transcription = result[0] if result[0] else {}

        # Update the transcription with new values and edited_at timestamp
        updated_transcription = {
            **current_transcription,
            "note_title": note_title,
            "transcript_text": transcript_text,
            "edited_at": current_timestamp,
        }

        # Update the entire transcription JSON
        cursor.execute(
            f"""
            UPDATE {schema}.transcripts 
            SET transcription = %s::jsonb
            WHERE audio_key = %s
            """,
            (json.dumps(updated_transcription), audio_key),
        )

        conn.commit()
        logger.info(f"Updated note content for audio_key {audio_key}")

        return {"success": True, "audio_key": audio_key, "edited_at": current_timestamp}

    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in request body")
    except Exception as e:
        logger.error(f"Error editing note: {str(e)}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Error editing note")


@rt("/get-audio/{audio_key}")
def get_audio(request: Request, audio_key: str):
    schema = validate_schema(request.cookies.get("schema"))
    if not schema:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Get audio URL directly from s3_object_url
        cursor.execute(
            f"""
            SELECT metadata->>'s3_compressed_audio_url'
            FROM {schema}.audios 
            WHERE audio_key = %s AND deleted_at IS NULL
            """,
            (audio_key,),
        )
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail="Audio not found")

        s3_url = result[0]

        # Extract S3 key from s3:// URI
        if not s3_url.startswith("s3://"):
            raise ValueError("Invalid S3 URI format")

        s3_key = s3_url.replace("s3://" + AWS_S3_BUCKET + "/", "")
        logger.info(f"Fetching audio from S3 with key: {s3_key}")

        try:
            response = s3.get_object(Bucket=AWS_S3_BUCKET, Key=s3_key)
            audio_data = response["Body"].read()

            return StreamingResponse(
                io.BytesIO(audio_data),
                media_type="audio/webm",
                headers={
                    "Accept-Ranges": "bytes",
                },
            )
        except Exception as e:
            logger.error(
                f"Error fetching from S3 - Bucket: {AWS_S3_BUCKET}, Key: {s3_key}"
            )
            raise HTTPException(
                status_code=500, detail=f"Error fetching audio: {str(e)}"
            )

    except ValueError as e:
        logger.error(f"Invalid S3 URI format: {str(e)}")
        raise HTTPException(status_code=500, detail="Invalid S3 URI format")
    except Exception as e:
        logger.error(f"Error in get_audio: {str(e)}")
        raise HTTPException(status_code=500, detail="Server error")


@rt("/api/chat", methods=["POST"])
async def chat(request: Request):
    schema = validate_schema(request.cookies.get("schema"))
    if not schema:
        raise HTTPException(status_code=401, detail="Not authenticated")

    if not rate_limiter.is_allowed(schema):
        raise HTTPException(status_code=429, detail="Too many requests")

    try:
        data = await request.json()
        chat_id = data.get("chat_id")
        message = data.get("message")

        if not message:
            raise HTTPException(status_code=400, detail="Message is required")

        # First, ensure chat exists or create it
        cursor.execute(
            f"""
            INSERT INTO {schema}.chats (chat_id, title)
            VALUES (%s, %s)
            ON CONFLICT (chat_id) DO NOTHING
            """,
            (chat_id, "New Chat"),
        )

        # Find relevant context from user's notes
        relevant_chunks = find_relevant_context(schema, cursor, message)
        context_chunks = []
        source_keys = []

        for chunk in relevant_chunks:
            if chunk[2] > 0.7:  # Only use if similarity > 0.7
                context_chunks.append(chunk[0])
                source_keys.append(chunk[1])

        # Construct messages for GPT
        messages = [
            {
                "role": "system",
                "content": """You are Voice2Note's AI assistant, helping users understand their transcribed voice notes.
                Provide clear, concise responses and when referencing information, mention which note it comes from.
                Avoid verbosity and output the responses in a reading friendly format. Treat the user as 'You', since all 
                the questions will be about their notes.""",
            }
        ]

        if context_chunks:
            context_message = "Here are relevant parts of your notes:\n\n"
            for idx, chunk in enumerate(context_chunks):
                context_message += f"Note {idx + 1}:\n{chunk}\n\n"
            messages.append({"role": "system", "content": context_message})

        messages.append({"role": "user", "content": message})

        # Get response from OpenAI
        response = get_chat_completion(messages)

        # Store user message
        cursor.execute(
            f"""
            INSERT INTO {schema}.chat_messages (chat_id, role, content)
            VALUES (%s, 'user', %s)
            """,
            (chat_id, message),
        )

        # Store assistant response with sources
        cursor.execute(
            f"""
            INSERT INTO {schema}.chat_messages (chat_id, role, content, source_refs)
            VALUES (%s, 'assistant', %s, %s)
            """,
            (
                chat_id,
                response,
                json.dumps({"sources": source_keys}) if source_keys else None,
            ),
        )

        # Check if we should generate a title
        cursor.execute(
            f"""
            SELECT COUNT(*), title FROM {schema}.chat_messages 
            JOIN {schema}.chats ON chat_messages.chat_id = chats.chat_id
            WHERE chat_messages.chat_id = %s
            GROUP BY title
            """,
            (chat_id,),
        )
        result = cursor.fetchone()

        if result and result[0] >= 3 and result[1] == "New Chat":
            # Get recent messages for title generation
            cursor.execute(
                f"""
                SELECT role, content 
                FROM {schema}.chat_messages 
                WHERE chat_id = %s 
                ORDER BY created_at ASC 
                LIMIT 3
                """,
                (chat_id,),
            )
            title_messages = [
                {"role": m[0], "content": m[1]} for m in cursor.fetchall()
            ]

            new_title = generate_chat_title(title_messages)

            cursor.execute(
                f"""
                UPDATE {schema}.chats 
                SET title = %s 
                WHERE chat_id = %s
                """,
                (new_title, chat_id),
            )

        conn.commit()

        return {
            "response": response,
            "references": (
                json.dumps({"sources": source_keys}) if source_keys else None
            ),
        }

    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@rt("/api/delete-chat/{chat_id}", methods=["POST"])
async def delete_chat(request: Request, chat_id: str):
    schema = validate_schema(request.cookies.get("schema"))
    if not schema:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Verify chat exists
        cursor.execute(
            f"""
            SELECT 1 FROM {schema}.chats 
            WHERE chat_id = %s 
            AND deleted_at IS NULL
            """,
            (chat_id,),
        )

        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Chat not found")

        # Soft delete
        cursor.execute(
            f"""
            UPDATE {schema}.chats 
            SET deleted_at = CURRENT_TIMESTAMP 
            WHERE chat_id = %s
            """,
            (chat_id,),
        )

        conn.commit()
        return {"success": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat: {str(e)}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Error deleting chat")


@rt("/chat_{chat_id}")
def chat_detail(request: Request, chat_id: str):
    schema = validate_schema(request.cookies.get("schema"))
    if not schema:
        return RedirectResponse(url="/login", status_code=303)

    # Get chat details and messages
    cursor.execute(
        f"""
        SELECT chat_id, title, created_at 
        FROM {schema}.chats 
        WHERE chat_id = %s AND deleted_at IS NULL
        """,
        (chat_id,),
    )
    chat = cursor.fetchone()

    messages = []
    if chat:
        cursor.execute(
            f"""
            SELECT 
                role, 
                content, 
                source_refs,
                TO_CHAR(created_at, 'HH24:MI') as time
            FROM {schema}.chat_messages 
            WHERE chat_id = %s 
            ORDER BY created_at ASC
            """,
            (chat_id,),
        )
        messages = cursor.fetchall()

    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Chat - Voice2Note"),
            Link(
                rel="stylesheet",
                href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css",
            ),
            Style(get_common_styles()),
            Style(
                """
                .chat-container {
                    width: 90%;
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    height: 90vh;
                    display: flex;
                    flex-direction: column;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                }

                .chat-header {
                    padding: 15px 20px;
                    background: navy;
                    font-family: Arial, sans-serif;
                    color: white;
                    border-radius: 8px 8px 0 0;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .chat-title {
                    display: flex;
                    align-items: center;
                    font-family: Arial, sans-serif;
                    gap: 10px;
                    font-size: 1em;  /* Reduced from 1.2em */
                    margin: 0;
                }

                .chat-title-input {
                    background: transparent;
                    border: 1px solid rgba(255,255,255,0.3);
                    color: white;
                    padding: 5px 10px;
                    border-radius: 4px;
                    font-size: 1em;
                    width: 100%;
                    display: none;
                }

                .chat-title-input:focus {
                    outline: none;
                    border-color: white;
                }

                .chat-title-text {
                    margin: 0;
                    padding: 5px 10px;
                    font-size: 1.1em;  /* Controlled size for the title text */
                    font-weight: normal;  /* Remove bold if too heavy */
                }

                .chat-title h1 {
                    font-size: 1.1em;  /* Control the h1 size */
                    margin: 0;
                    font-weight: 500;  /* Semi-bold instead of bold */
                }

                .edit-mode .chat-title-text {
                    display: none;
                }

                .edit-mode .chat-title-input {
                    display: block;
                }

                .chat-actions {
                    display: flex;
                    gap: 10px;
                }

                .action-btn {
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                    padding: 5px;
                    font-size: 1.1em;
                    opacity: 0.8;
                    transition: opacity 0.2s;
                }

                .action-btn:hover {
                    opacity: 1;
                }

                .messages-container {
                    flex: 1;
                    overflow-y: auto;
                    padding: 20px;
                    display: flex;
                    flex-direction: column;
                }

                .message {
                    max-width: 80%;
                    margin-bottom: 20px;
                    padding: 10px 15px;
                    border-radius: 8px;
                    position: relative;
                }

                .user-message {
                    background: #E3F2FD;
                    align-self: flex-end;
                    margin-left: 20%;
                }

                .assistant-message {
                    background: #F5F5F5;
                    align-self: flex-start;
                    margin-right: 20%;
                }

                .message-content {
                    margin: 0;
                    line-height: 1.4;
                    white-space: pre-wrap;
                }

                .message-time {
                    font-size: 0.8em;
                    color: #666;
                    margin-top: 5px;
                    text-align: right;
                }

                .input-container {
                    padding: 20px;
                    border-top: 1px solid #eee;
                    display: flex;
                    gap: 10px;
                }

                .message-input {
                    flex: 1;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    resize: none;
                    min-height: 44px;
                    max-height: 200px;
                }

                .send-btn {
                    background: navy;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    cursor: pointer;
                    transition: background-color 0.2s;
                }

                .send-btn:hover {
                    background: #000080;
                }

                .send-btn:disabled {
                    background: #ccc;
                    cursor: not-allowed;
                }

                .empty-messages {
                    text-align: center;
                    color: #666;
                    margin: auto;
                }

                .loading-message {
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    color: #666;
                    margin: 20px 0;
                }

                .spinner {
                    font-size: 1.2em;
                }

                /* Landscape mode */
                @media (max-height: 600px) and (orientation: landscape) {
                    .chat-container {
                        height: auto;
                        min-height: 100vh;
                    }

                    .messages-container {
                        max-height: 60vh;
                    }

                    .message {
                        margin-bottom: 24px;
                    }
                }

                .load-more-container {
                    text-align: center;
                    padding: 10px 0;
                }

                .load-more-btn {
                    background: navy;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                    cursor: pointer;
                }

                .load-more-btn:hover {
                    background: #004080;
                }

                .source-loading {
                    margin-left: 8px;
                    color: #666;
                }
                """
            ),
        ),
        Script(
            """
            // Add at the top of chat_detail Script
            let messageOffset = 0;
            const messageLimit = 20;
            let isProcessing = false;

            async function sendMessage() {
                if (isProcessing) return;
                
                const input = document.querySelector('.message-input');
                const content = input.value.trim();
                if (!content) return;
                
                isProcessing = true;
                const sendBtn = document.querySelector('.send-btn');
                sendBtn.disabled = true;
                
                addMessage(content, 'user');
                input.value = '';
                adjustTextarea(input);
                
                showLoadingSpinner();
                
                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            chat_id: window.location.pathname.split('_')[1],
                            message: content
                        })
                    });

                    removeLoadingSpinner();
                    
                    if (!response.ok) {
                        throw new Error(await response.text());
                    }

                    const data = await response.json();
                    if (!data.response) {
                        throw new Error('Invalid response format');
                    }

                    addMessage(data.response, 'assistant', data.references);

                } catch (error) {
                    console.error('Error:', error);
                    removeLoadingSpinner();
                    addMessage('An error occurred. Please try again.', 'assistant');
                } finally {
                    isProcessing = false;
                    sendBtn.disabled = false;
                }
            }

            function addMessage(content, role, references = null, time = null) {
                const container = document.querySelector('.messages-container');
                const message = document.createElement('div');
                message.className = `message ${role}-message`;
                
                let html = `<div class="message-content">${content}</div>`;
                
                if (time) {
                    html += `<div class="message-time">${time}</div>`;
                }
                
                message.innerHTML = html;
                container.appendChild(message);
                container.scrollTop = container.scrollHeight;
            }

            function adjustTextarea(el) {
                el.style.height = '44px';
                el.style.height = (el.scrollHeight) + 'px';
            }

            function showLoadingSpinner() {
                const container = document.querySelector('.messages-container');
                const loading = document.createElement('div');
                loading.className = 'loading-message';
                loading.innerHTML = `
                    <div class="spinner">
                        <i class="fas fa-circle-notch fa-spin"></i>
                    </div>
                    <p>Thinking...</p>
                `;
                container.appendChild(loading);
                container.scrollTop = container.scrollHeight;
            }

            function removeLoadingSpinner() {
                const spinner = document.querySelector('.loading-message');
                if (spinner) spinner.remove();
            }

            function showSourceLoading(event) {
                const link = event.currentTarget;
                const loadingSpinner = link.nextElementSibling;
                loadingSpinner.style.display = 'inline-block';
            }

            function toggleTitleEdit(show) {
                const titleContainer = document.querySelector('.chat-title');
                const titleText = titleContainer.querySelector('.chat-title-text');
                const titleInput = titleContainer.querySelector('.chat-title-input');
                
                if (show) {
                    titleContainer.classList.add('edit-mode');
                    titleInput.value = titleText.textContent;
                    titleInput.focus();
                } else {
                    titleContainer.classList.remove('edit-mode');
                }
            }

            async function saveChatTitle(chatId) {
                const titleContainer = document.querySelector('.chat-title');
                const titleInput = titleContainer.querySelector('.chat-title-input');
                const titleText = titleContainer.querySelector('.chat-title-text');
                const newTitle = titleInput.value.trim();

                if (!newTitle) {
                    alert("Title cannot be empty");
                    return;
                }

                try {
                    const response = await fetch(`/api/edit-chat-title/${chatId}`, {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                        },
                        body: JSON.stringify({ title: newTitle }),
                    });

                    if (!response.ok) {
                        throw new Error("Failed to update chat title");
                    }

                    const data = await response.json();
                    titleText.textContent = data.new_title;
                    toggleTitleEdit(false);
                } catch (error) {
                    console.error("Error updating chat title:", error);
                    alert("Failed to update chat title");
                }
            }

            // Event listeners
            document.addEventListener('DOMContentLoaded', () => {
                const input = document.querySelector('.message-input');
                const container = document.querySelector('.messages-container');
                
                container.scrollTop = container.scrollHeight;
                
                input.addEventListener('input', (e) => {
                    adjustTextarea(e.target);
                });
                
                input.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        sendMessage();
                    }
                });

                const titleInput = document.querySelector('.chat-title-input');
                if (titleInput) {
                    titleInput.addEventListener('keydown', (e) => {
                        const chatId = window.location.pathname.split('_')[1];
                        if (e.key === 'Enter') {
                            e.preventDefault();
                            saveChatTitle(chatId);
                        } else if (e.key === 'Escape') {
                            toggleTitleEdit(false);
                        }
                    });
                }
            });
            """
        ),
        Body(
            Div(
                Div(
                    Div(
                        I(cls="fas fa-robot"),
                        Div(
                            H1(
                                chat[1] if chat else "Ask your notes!",
                                cls="chat-title-text",
                            ),
                            Input(
                                type="text",
                                cls="chat-title-input",
                                value=chat[1] if chat else "Ask your notes!",
                            ),
                            cls="chat-title",
                        ),
                        Div(
                            Button(
                                I(cls="fas fa-pencil-alt"),
                                cls="action-btn edit-title-btn",
                                title="Edit chat title",
                                onclick="toggleTitleEdit(true)",
                            ),
                            Button(
                                I(cls="fas fa-trash"),
                                cls="action-btn delete-btn",
                                title="Delete chat",
                                onclick="deleteChat()",
                            ),
                            A(
                                Button(
                                    I(cls="fas fa-arrow-left"),
                                    cls="action-btn",
                                    title="Back to notes",
                                ),
                                href="/notes",
                            ),
                            cls="chat-actions",
                        ),
                        cls="chat-header",
                    ),
                    Div(
                        *(
                            [
                                Button(
                                    "Load More",
                                    cls="load-more-btn",
                                    onclick="loadMoreMessages()",
                                )
                            ]
                            if len(messages) >= 20
                            else []
                        ),
                        cls="load-more-container",
                    ),
                    Div(
                        *(
                            [
                                Div(
                                    Div(msg[1], cls="message-content"),  # content
                                    Div(msg[3], cls="message-time"),  # time
                                    cls=f"message {msg[0]}-message",
                                )
                                for msg in messages
                            ]
                            if messages
                            else [
                                Div(
                                    "Ask anything about your notes. Start the conversation by typing a message below.",
                                    cls="empty-messages",
                                )
                            ]
                        ),
                        cls="messages-container",
                    ),
                    Div(
                        Textarea(
                            placeholder="Type your message...",
                            cls="message-input",
                            rows="1",
                        ),
                        Button(
                            I(cls="fas fa-paper-plane"),
                            cls="send-btn",
                            onclick="sendMessage()",
                        ),
                        cls="input-container",
                    ),
                    cls="chat-container",
                ),
            ),
        ),
    )


@rt("/api/chat/{chat_id}/messages")
async def get_chat_messages(request: Request, chat_id: str, offset: int = 0):
    schema = validate_schema(request.cookies.get("schema"))
    if not schema:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        cursor.execute(
            f"""
            SELECT role, content, source_refs, 
                    TO_CHAR(created_at, 'HH24:MI') as time
            FROM {schema}.chat_messages 
            WHERE chat_id = %s
            ORDER BY created_at DESC
            LIMIT 20 OFFSET %s
            """,
            (chat_id, offset),
        )
        messages = cursor.fetchall()

        return [
            {
                "role": msg[0],
                "content": msg[1],
                "source_refs": msg[2],
                "time": msg[3],
            }
            for msg in messages
        ]

    except Exception as e:
        logger.error(f"Error fetching messages: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching messages")


@rt("/api/edit-chat-title/{chat_id}", methods=["POST"])
async def edit_chat_title(request: Request, chat_id: str):
    schema = validate_schema(request.cookies.get("schema"))
    if not schema:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Get the updated title from the request
        body = await request.json()
        new_title = body.get("title")

        if not new_title or new_title.strip() == "":
            raise HTTPException(status_code=400, detail="Title cannot be empty")

        # Update the chat title
        cursor.execute(
            f"""
            UPDATE {schema}.chats 
            SET title = %s 
            WHERE chat_id = %s AND deleted_at IS NULL
            """,
            (new_title, chat_id),
        )
        conn.commit()
        logger.info(f"Updated chat title for chat_id {chat_id} to '{new_title}'")

        return {"success": True, "chat_id": chat_id, "new_title": new_title}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error editing chat title: {str(e)}")
        conn.rollback()
        raise HTTPException(status_code=500, detail="Error editing chat title")


serve()
