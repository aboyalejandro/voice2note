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
from contextlib import contextmanager
import io
from starlette.responses import StreamingResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)

logger = logging.getLogger("voice2note")

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

    /* Common responsive adjustments */
    @media (max-width: 768px) {
        body {
            padding: 10px;
        }
        
        .container {
            width: 95%;
            padding: 15px;
            margin: 10px auto;
        }

        /* Auth pages responsive styles */
        .auth-container {
            width: 95%;
            padding: 15px;
            margin: 10px;
        }

        .auth-title {
            font-size: 20px;
        }

        .form-input {
            padding: 8px;
            font-size: 14px;
        }

        .auth-btn {
            padding: 10px 15px;
            font-size: 14px;
        }

        /* Home page responsive styles */
        .controls {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 15px;
        }

        .record-btn, .stop-btn, .upload-btn {
            font-size: 32px;
            padding: 8px;
            margin: 0;
        }

        .audio-player {
            width: 100%;
            max-width: 300px;
        }

        .save-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }

        .save-btn, .notes-btn {
            width: 100%;
            max-width: 200px;
        }

        /* Notes page responsive styles */
        .note {
            padding: 12px;
        }

        .note-header {
            flex-direction: column;
            gap: 10px;
        }

        .note-actions {
            justify-content: flex-start;
            width: 100%;
        }

        .note-info {
            width: 100%;
        }

        .note-title {
            font-size: 16px;
            word-break: break-word;
        }

        .note-preview {
            font-size: 13px;
        }

        .search-container {
            flex-direction: column;
            gap: 10px;
        }

        .date-field {
            flex-direction: column;
            width: 100%;
        }

        .date-input {
            width: 100%;
        }

        .keyword-field {
            width: 100%;
        }

        .button-field {
            flex-direction: row;
            justify-content: space-between;
            width: 100%;
        }

        .search-btn, .clear-btn {
            flex: 1;
        }

        /* Note detail page responsive styles */
        .note-transcription {
            font-size: 14px;
            line-height: 1.4;
        }

        .form-textarea {
            min-height: 200px;
            font-size: 14px;
        }

        .form-buttons {
            flex-direction: column;
            gap: 10px;
        }

        .save-btn, .cancel-btn {
            width: 100%;
        }

        .back-button {
            margin-top: 20px;
            margin-bottom: 15px;
            font-size: 14px;
            padding: 8px 12px;
        }

        /* Audio player responsive styles */
        .audio-player {
            width: 100%;
            max-width: none;
        }

        /* Logout button positioning */
        .logout-btn {
            position: fixed;
            top: 10px;
            right: 10px;
            z-index: 1000;
        }
    }

    /* Small phones */
    @media (max-width: 380px) {
        .auth-title {
            font-size: 18px;
        }

        .record-btn, .stop-btn, .upload-btn {
            font-size: 28px;
            padding: 6px;
        }

        .note-title {
            font-size: 14px;
        }

        .note-preview {
            font-size: 12px;
        }
    }

    /* Landscape orientation adjustments */
    @media (max-height: 600px) and (orientation: landscape) {
        body {
            height: auto;
            min-height: 100vh;
        }

        .container {
            margin: 60px auto;
        }

        .audio-wrapper {
            margin: 10px 0;
        }

        .controls {
            margin: 10px 0;
        }
    }

    /* Dark mode detection */
    @media (prefers-color-scheme: dark) {
        body {
            background-color: #1a1a1a;
            color: #ffffff;
        }

        .container, .auth-container {
            background-color: #2d2d2d;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }

        .note {
            background-color: #3d3d3d;
        }

        .note-title {
            color: #66b3ff;
        }

        .form-input, .form-textarea {
            background-color: #3d3d3d;
            color: #ffffff;
            border-color: #4d4d4d;
        }

        .search-container {
            background-color: #3d3d3d;
        }
    }
    """


def create_user_schema(user_id: int):
    """Creates a new schema and required tables for a user"""
    logger.info(f"Starting schema creation for user_id: {user_id}")
    try:
        # Create schema
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS user_{user_id}")
        logger.info(f"Schema user_{user_id} created successfully")

        # Create audios table
        cursor.execute(
            f"""
            CREATE TABLE user_{user_id}.audios (
                audio_id serial4 NOT NULL,
                audio_key varchar(15) NOT NULL,
                user_id int4 NOT NULL,
                s3_object_url text NOT NULL,
                audio_type varchar(8) NOT NULL,
                created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
                deleted_at timestamp NULL,
                metadata jsonb NULL,
                CONSTRAINT audios_audio_key_key UNIQUE (audio_key),
                CONSTRAINT audios_audio_type_check CHECK (
                    audio_type = ANY (ARRAY['recorded', 'uploaded'])
                ),
                CONSTRAINT audios_pkey PRIMARY KEY (audio_id)
            )
        """
        )

        logger.info(f"Audios table created for user_{user_id}")

        # Create transcripts table
        cursor.execute(
            f"""
            CREATE TABLE user_{user_id}.transcripts (
                transcript_id serial4 NOT NULL,
                audio_key varchar(255) NOT NULL,
                s3_object_url text NULL,
                transcription jsonb NULL,
                created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
                deleted_at timestamp NULL,
                CONSTRAINT transcripts_pkey PRIMARY KEY (transcript_id)
            )
        """
        )

        logger.info(f"Transcripts table created for user_{user_id}")

        # Create indexes
        cursor.execute(
            f"""
            CREATE INDEX idx_audios_audio_id ON user_{user_id}.audios USING btree (audio_id);
            CREATE INDEX idx_transcripts_audio_id ON user_{user_id}.transcripts USING btree (audio_key);
            CREATE INDEX idx_transcripts_transcript_id ON user_{user_id}.transcripts USING btree (transcript_id)
        """
        )

        logger.info(f"Indexes created for user_{user_id} schema")

        # Add foreign key constraints
        cursor.execute(
            f"""
            ALTER TABLE user_{user_id}.audios ADD CONSTRAINT fk_user_id 
            FOREIGN KEY (user_id) REFERENCES public.users(user_id);
            
            ALTER TABLE user_{user_id}.transcripts ADD CONSTRAINT transcripts_audio_key_fkey 
            FOREIGN KEY (audio_key) REFERENCES user_{user_id}.audios(audio_key)
        """
        )

        logger.info(f"Foreign key constraints added for user_{user_id}")

        conn.commit()
        logger.info(f"Schema creation completed successfully for user_{user_id}")
        return True

    except Exception as e:
        conn.rollback()
        logging.error(f"Error creating schema for user_{user_id}: {str(e)}")
        raise


@contextmanager
def use_user_schema(user_id: int):
    """Context manager to temporarily switch to a user's schema"""
    try:
        cursor.execute(f"SET search_path TO user_{user_id}")
        yield
    finally:
        cursor.execute("SET search_path TO public")


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
    user_id = get_current_user_id(request)
    if not user_id:
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
            """
                ),
            ),
        ),
    )


@rt("/notes")
def notes(request, start_date: str = None, end_date: str = None, keyword: str = None):
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    # Build query based on filters
    query = """
        SELECT 
            audios.audio_key,
            TO_CHAR(audios.created_at, 'MM/DD') as note_date,
            COALESCE(transcription->>'note_title','Transcribing note...') as note_title,
            COALESCE(transcription->>'summary_text','Your audio is being transcribed. It will show up in here when is finished.') as note_summary,
            COALESCE(metadata->>'duration', '00:00:00') as duration
        FROM audios
        LEFT JOIN transcripts ON audios.audio_key = transcripts.audio_key
        WHERE audios.deleted_at IS NULL
    """
    query_params = []

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
        query += " AND (transcription->>'transcript_text' ILIKE %s OR transcription->>'note_title' ILIKE %s)"
        query_params.extend([f"%{keyword}%", f"%{keyword}%"])

    query += " ORDER BY audios.created_at DESC"

    # Execute query in user's schema
    with use_user_schema(user_id):
        cursor.execute(query, query_params)
        notes = cursor.fetchall()

    # Create search form with both date and keyword fields
    search_form = Div(
        Form(
            Div(
                # Date inputs with calendar icon
                Div(
                    I(cls="fas fa-calendar", style="color: navy;"),
                    Input(
                        type="date",
                        name="start_date",
                        cls="date-input",
                        value=start_date or "",
                        title="From date",
                    ),
                    "→",  # Arrow between dates
                    Input(
                        type="date",
                        name="end_date",
                        cls="date-input",
                        value=end_date or "",
                        title="To date",
                    ),
                    cls="date-field",
                ),
                # Search input with search icon
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
                    Button("\u2192", cls="view-btn"),
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
                
                //* Search form styles */
                .search-wrapper {
                    margin-bottom: 20px;
                    width: 100%;
                }
                .search-form {
                    width: 100%;
                }
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
                }
                .date-input {
                    padding: 6px;
                    border: 1px solid navy;
                    border-radius: 4px;
                    color: #333;
                    width: 130px;
                    font-size: 14px;
                }
                .date-input::-webkit-calendar-picker-indicator {
                    cursor: pointer;
                }
                .keyword-field {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    flex-grow: 1;
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

                @media (max-width: 768px) {
                    .search-container {
                        flex-direction: column;
                        align-items: stretch;
                        gap: 12px;
                    }
                    .date-field {
                        flex-wrap: wrap;
                        justify-content: space-between;
                    }
                    .keyword-field {
                        width: 100%;
                    }
                    .button-field {
                        justify-content: stretch;
                    }
                    .search-btn, .clear-btn {
                        flex: 1;
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
                A("\u2190", href="/", cls="back-button"),
                Div(H1("Your Last Notes", cls="title")),
                Div(
                    search_form,
                    *(
                        note_cards
                        if note_cards
                        else "Your notes will show up here when you record or upload them."
                    ),
                    cls="container",
                ),
            ),
        ),
    )


@rt("/note_{audio_key}")
def note_detail(request: Request, audio_key: str):
    # Get current user_id from session
    user_id = get_current_user_id(request)
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    # Query note details in user's schema
    with use_user_schema(user_id):
        cursor.execute(
            """
            SELECT 
                audios.audio_key,
                TO_CHAR(audios.created_at, 'MM/DD') as note_date,
                COALESCE(transcription->>'note_title','Transcribing note...') as note_title,
                COALESCE(transcription->>'transcript_text','Your audio is being transcribed. It will show up in here when is finished.') as note_transcription,
                COALESCE(metadata->>'duration', '00:00:00') as duration
            FROM audios
            LEFT JOIN transcripts ON audios.audio_key = transcripts.audio_key
            WHERE audios.audio_key = %s
            AND audios.deleted_at IS NULL
            """,
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
                    const audioPlayer = document.getElementById('audio-player');
                    
                    if (!isPlaying) {
                        try {
                            playBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                            
                            // Fetch the audio file
                            const response = await fetch(`/get-audio/${audioKey}`);
                            if (!response.ok) throw new Error('Failed to fetch audio');
                            
                            const blob = await response.blob();
                            const audioUrl = URL.createObjectURL(blob);
                            
                            // Create a new audio element each time
                            const newAudioPlayer = document.createElement('audio');
                            newAudioPlayer.id = 'audio-player';
                            newAudioPlayer.className = 'audio-player';
                            
                            // Replace old audio player
                            const oldAudioPlayer = audioPlayer;
                            oldAudioPlayer.parentNode.replaceChild(newAudioPlayer, oldAudioPlayer);
                            
                            // Set source and try to play
                            newAudioPlayer.src = audioUrl;
                            newAudioPlayer.style.display = 'block';
                            durationDisplay.style.display = 'none';
                            
                            // Add error handler
                            newAudioPlayer.onerror = (e) => {
                                console.error('Audio playback error:', e);
                                alert('This audio format might not be supported by your browser. Try downloading the file instead.');
                                playBtn.innerHTML = '<i class="fas fa-play"></i>';
                                isPlaying = false;
                            };
                            
                            // Try playing
                            const playPromise = newAudioPlayer.play();
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
                            newAudioPlayer.onended = () => {
                                playBtn.innerHTML = '<i class="fas fa-play"></i>';
                                newAudioPlayer.style.display = 'none';
                                durationDisplay.style.display = 'block';
                                isPlaying = false;
                            };
                        } catch (error) {
                            console.error('Error playing audio:', error);
                            alert('Failed to play audio. You may need to download it instead.');
                            playBtn.innerHTML = '<i class="fas fa-play"></i>';
                            isPlaying = false;
                        }
                    } else {
                        // Pause audio
                        audioPlayer.pause();
                        playBtn.innerHTML = '<i class="fas fa-play"></i>';
                        audioPlayer.style.display = 'none';
                        durationDisplay.style.display = 'block';
                        isPlaying = false;
                    }
                }
            """
            ),
        ),
        Body(
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
                            P(
                                note[4] if note[4] else "0.00s",
                                cls="note-duration",
                                id="duration-display",
                            ),
                            Audio(
                                id="audio-player",
                                cls="audio-player",
                                style="display: none;",
                            ),
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
                        cls="note-header",
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
    user_id = get_current_user_id(request)
    if not user_id:
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
        audio_key = f"{user_id}_{timestamp}"
        s3_key = f"user_{user_id}/audios/raw/{audio_key}.{file_extension}"
        s3_url = f"s3://{AWS_S3_BUCKET}/{s3_key}"

        logging.info(f"Saving {audio_type} audio file with key: {audio_key}")

        # Insert record using user schema
        query = """
            INSERT INTO audios (audio_key, user_id, s3_object_url, audio_type, created_at)
            VALUES (%s, %s, %s, %s, %s) 
            RETURNING audio_key
        """
        query_params = [
            audio_key,
            user_id,
            s3_url,
            audio_type,
            datetime.now(),
        ]

        with use_user_schema(user_id):
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
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Switch to user schema for all database operations
        with use_user_schema(user_id):
            # Check if note exists
            cursor.execute(
                "SELECT 1 FROM audios WHERE audio_key = %s AND deleted_at IS NULL",
                (audio_key,),
            )

            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Note not found")

            # Soft delete
            cursor.execute(
                """
                WITH audio_update AS (
                    UPDATE audios 
                    SET deleted_at = CURRENT_TIMESTAMP 
                    WHERE audio_key = %s
                )
                UPDATE transcripts 
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
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Get the updated content from request body
        body = await request.json()
        note_title = body.get("note_title")
        transcript_text = body.get("transcript_text")
        current_timestamp = datetime.now().isoformat()

        # Switch to user schema
        with use_user_schema(user_id):
            # Verify note exists and belongs to user
            cursor.execute(
                "SELECT transcription FROM transcripts WHERE audio_key = %s",
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
                """
                UPDATE transcripts 
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
    user_id = get_current_user_id(request)
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        # Get audio URL directly from s3_object_url
        with use_user_schema(user_id):
            cursor.execute(
                """
                SELECT metadata->>'s3_compressed_audio_url'
                FROM audios 
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


serve()
