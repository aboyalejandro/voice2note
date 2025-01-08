"""
API route handlers for Voice2Note.

This module handles all API endpoints including:
- Authentication (login, signup, password reset)
- Chat functionality (messages, title editing)
- Note management (editing, deletion)
- Audio file handling
- Session management

Each route handler includes proper error handling and database transaction management.
"""

from fasthtml.common import *
from datetime import datetime, timedelta
from starlette.responses import JSONResponse, RedirectResponse, StreamingResponse
from starlette.exceptions import HTTPException
import bcrypt
import uuid
from frontend.styles import Styles
from backend.config import logger, s3, AWS_S3_BUCKET
from backend.llm import LLM, RateLimiter
import json
import io

# Initialize LLM
rate_limiter = RateLimiter(max_requests=5, window=60)
llm = LLM()

# Initialize styles
styles = Styles()


def setup_api_routes(app, db):
    """
    Configure all API routes for the application.

    Args:
        app: The FastAPI application instance
        db: DatabaseManager instance for connection pooling

    Returns:
        app: The configured application with all routes added
    """

    # Authentication Routes
    @app.route("/api/login", methods=["POST"])
    async def api_login(request):
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        success, user_id = db.verify_user_credentials(username, password)
        if not success:
            return Html(
                Head(
                    Meta(
                        name="viewport", content="width=device-width, initial-scale=1.0"
                    ),
                    Title("Login Error - Voice2Note"),
                    Style(styles.common()),
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
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    session_id = str(uuid.uuid4())
                    expires_at = datetime.now() + timedelta(days=7)

                    cur.execute(
                        """
                        INSERT INTO sessions (session_id, user_id, expires_at)
                        VALUES (%s, %s, %s)
                        """,
                        (session_id, user_id, expires_at),
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
                        value=f"user_{user_id}",
                        httponly=True,
                        max_age=7 * 24 * 60 * 60,
                        secure=True,
                        samesite="lax",
                    )
            return response

        except Exception as e:
            logger.error(f"Error in login: {str(e)}")
            raise HTTPException(status_code=500, detail="Login failed")

    @app.route("/api/logout", methods=["POST"])
    async def api_logout(request):
        session_id = request.cookies.get("session_id")
        if session_id:
            with db.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE sessions SET deleted_at = CURRENT_TIMESTAMP WHERE session_id = %s",
                        (session_id,),
                    )
                    conn.commit()
            logger.info(f"Finished session: {session_id}")

        response = RedirectResponse(url="/login", status_code=303)
        response.delete_cookie(key="session_id")
        return response

    @app.route("/api/signup", methods=["POST"])
    async def api_signup(request):
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # Check if username exists
                cur.execute(
                    "SELECT username FROM users WHERE username = %s", (username,)
                )
                if cur.fetchone():
                    return Html(
                        Head(
                            Meta(
                                name="viewport",
                                content="width=device-width, initial-scale=1.0",
                            ),
                            Title("Sign Up Error - Voice2Note"),
                            Style(styles.common()),
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
                    hashed_password = bcrypt.hashpw(
                        password.encode("utf-8"), bcrypt.gensalt()
                    )

                    cur.execute(
                        """
                        INSERT INTO users (username, hashed_password, created_at)
                        VALUES (%s, %s, CURRENT_TIMESTAMP)
                        RETURNING user_id
                        """,
                        (username, hashed_password.decode("utf-8")),
                    )
                    user_id = cur.fetchone()[0]
                    conn.commit()

                    # Create schema
                    db.create_user_schema(user_id)

                    # Create session
                    session_id = str(uuid.uuid4())
                    expires_at = datetime.now() + timedelta(days=7)

                    cur.execute(
                        """
                        INSERT INTO sessions (session_id, user_id, expires_at)
                        VALUES (%s, %s, %s)
                        """,
                        (session_id, user_id, expires_at),
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
                    response.set_cookie(
                        key="schema",
                        value=f"user_{user_id}",
                        httponly=True,
                        max_age=7 * 24 * 60 * 60,
                        secure=True,
                        samesite="lax",
                    )
                    return response

                except Exception as e:
                    logger.error(f"Error in signup: {str(e)}")
                    raise HTTPException(status_code=500, detail="Signup failed")

    @app.route("/api/request-reset", methods=["POST"])
    async def request_reset(request):
        form = await request.form()
        username = form.get("username")

        with db.get_connection() as conn:  # App Pool
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id FROM users WHERE username = %s", (username,)
                )
                user = cur.fetchone()

        if not user:
            return Html(
                Head(
                    Meta(
                        name="viewport", content="width=device-width, initial-scale=1.0"
                    ),
                    Title("Reset Password Error"),
                    Style(styles.common()),
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

        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users 
                    SET reset_token = %s, reset_token_expires = %s 
                    WHERE username = %s
                    """,
                    (reset_token, expires_at, username),
                )
                conn.commit()

        reset_link = f"/reset-password/{reset_token}"
        return Html(
            Head(
                Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
                Title("Reset Password"),
                Style(styles.common()),
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

    @app.route("/api/reset-password", methods=["POST"])
    async def reset_password_submit(request):
        form = await request.form()
        token = form.get("token")
        new_password = form.get("password")

        # Verify token and get user
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT user_id 
                    FROM users 
                    WHERE reset_token = %s 
                    AND reset_token_expires > CURRENT_TIMESTAMP
                    """,
                    (token,),
                )
                user = cur.fetchone()

        if not user:
            return Html(
                Head(
                    Meta(
                        name="viewport", content="width=device-width, initial-scale=1.0"
                    ),
                    Title("Reset Error"),
                    Style(styles.common()),
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

        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE users 
                    SET hashed_password = %s, reset_token = NULL, reset_token_expires = NULL 
                    WHERE user_id = %s
                    """,
                    (hashed_password.decode("utf-8"), user[0]),
                )
                conn.commit()

        # Handle DB user password update
        db.handle_password_reset(user[0])

        return Html(
            Head(
                Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
                Title("Password Reset Success"),
                Style(styles.common()),
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

    # Chat Routes
    @app.route("/api/chat", methods=["POST"])
    async def chat(request: Request):
        schema = db.validate_schema(request.cookies.get("schema"))
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

            with db.get_schema_connection(schema) as conn:
                with conn.cursor() as cur:
                    # Create chat if doesn't exist
                    cur.execute(
                        f"""
                        INSERT INTO {schema}.chats (chat_id, title)
                        VALUES (%s, %s)
                        ON CONFLICT (chat_id) DO NOTHING
                        """,
                        (chat_id, "New Chat"),
                    )

                    # Find relevant context from user's notes
                    relevant_chunks = llm.find_relevant_context(schema, cur, message)
                    context_chunks = []
                    source_keys = []

                    for chunk in relevant_chunks:
                        if chunk[2] > 0.7:
                            context_chunks.append(chunk[0])
                            source_keys.append(chunk[1])

                    # Construct messages for GPT
                    messages = [
                        {
                            "role": "system",
                            "content": """You are Voice2Note's AI assistant, helping users understand their transcribed voice notes.
                            Provide clear, concise responses and when referencing information, mention only once and at the end of the message which note it comes from in this format: (Note 1). 
                            Only do the latter if asked something about a note.
                            Use titles, split paragraphs and bullet points to make the response more readable.
                            Avoid verbosity and output the responses in a reading friendly format. Treat the user as 'You', since all 
                            the questions will be about their notes.
                            Answer in the same language as the user's notes.""",
                        }
                    ]

                    if context_chunks:
                        context_message = "Here are relevant parts of your notes:\n\n"
                        for idx, chunk in enumerate(context_chunks):
                            context_message += f"Note {idx + 1}:\n{chunk}\n\n"
                        messages.append({"role": "system", "content": context_message})

                    messages.append({"role": "user", "content": message})

                    # Get response from OpenAI
                    response = llm.get_chat_completion(messages)

                    # Store user message
                    cur.execute(
                        f"""
                        INSERT INTO {schema}.chat_messages (chat_id, role, content)
                        VALUES (%s, 'user', %s)
                        """,
                        (chat_id, message),
                    )

                    # Store assistant response
                    cur.execute(
                        f"""
                        INSERT INTO {schema}.chat_messages (chat_id, role, content, source_refs)
                        VALUES (%s, 'assistant', %s, %s)
                        """,
                        (
                            chat_id,
                            response,
                            (
                                json.dumps({"sources": source_keys})
                                if source_keys
                                else None
                            ),
                        ),
                    )

                    # Check if we should generate a title (at least 3 messages required)
                    cur.execute(
                        f"""
                        SELECT COUNT(*), title FROM {schema}.chat_messages 
                        JOIN {schema}.chats ON chat_messages.chat_id = chats.chat_id
                        WHERE chat_messages.chat_id = %s
                        GROUP BY title
                        """,
                        (chat_id,),
                    )
                    result = cur.fetchone()

                    if result and result[0] >= 3 and result[1] == "New Chat":
                        # Get recent messages for title generation
                        cur.execute(
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
                            {"role": m[0], "content": m[1]} for m in cur.fetchall()
                        ]

                        new_title = llm.generate_chat_title(title_messages)

                        cur.execute(
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
            raise HTTPException(status_code=500, detail=str(e))

    @app.route("/api/delete-chat/{chat_id}", methods=["POST"])
    async def delete_chat(request: Request, chat_id: str):
        schema = db.validate_schema(request.cookies.get("schema"))
        if not schema:
            raise HTTPException(status_code=401, detail="Not authenticated")

        try:
            with db.get_schema_connection(schema) as conn:
                with conn.cursor() as cur:
                    # Verify chat exists
                    cur.execute(
                        f"""
                        SELECT 1 FROM {schema}.chats 
                        WHERE chat_id = %s 
                        AND deleted_at IS NULL
                        """,
                        (chat_id,),
                    )

                    if not cur.fetchone():
                        raise HTTPException(status_code=404, detail="Chat not found")

                    # Soft delete
                    cur.execute(
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
            raise HTTPException(status_code=500, detail="Error deleting chat")

    @app.route("/api/chat/{chat_id}/messages")
    async def get_chat_messages(request: Request, chat_id: str, offset: int = 0):
        schema = db.validate_schema(request.cookies.get("schema"))
        if not schema:
            raise HTTPException(status_code=401, detail="Not authenticated")

        try:
            with db.get_schema_connection(schema) as conn:
                with conn.cursor() as cur:
                    cur.execute(
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
                    messages = cur.fetchall()

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

    # Audio Routes
    @app.route("/api/get-audio/{audio_key}", methods=["GET"])
    async def get_audio(request):
        schema = db.validate_schema(request.cookies.get("schema"))
        if not schema:
            raise HTTPException(status_code=401, detail="Not authenticated")

        try:
            audio_key = request.path_params["audio_key"]

            with db.get_schema_connection(schema) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        SELECT metadata->>'s3_compressed_audio_url'
                        FROM {schema}.audios 
                        WHERE audio_key = %s 
                        AND deleted_at IS NULL
                        """,
                        (audio_key,),
                    )
                    result = cur.fetchone()

                    if not result or not result[0]:
                        raise HTTPException(status_code=404, detail="Audio not found")

                    s3_url = result[0]
                    if not s3_url.startswith("s3://"):
                        raise ValueError("Invalid S3 URI format")

                    s3_key = s3_url.replace(f"s3://{AWS_S3_BUCKET}/", "")

                    # Get file from S3
                    response = s3.get_object(Bucket=AWS_S3_BUCKET, Key=s3_key)
                    audio_data = response["Body"].read()

                    return StreamingResponse(
                        io.BytesIO(audio_data),
                        media_type="audio/webm",
                        headers={"Accept-Ranges": "bytes"},
                    )

        except Exception as e:
            logger.error(f"Error in get_audio: {str(e)}")
            raise HTTPException(status_code=500, detail="Server error")

    @app.route("/api/save-audio", methods=["POST"])
    async def save_audio(
        request: Request,
        audio_file: UploadFile,
        audio_type: str = Form(...),
    ):
        schema = db.validate_schema(request.cookies.get("schema"))
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
            user_id = schema.replace("user_", "")
            timestamp = int(datetime.now().timestamp())
            audio_key = f"{user_id}_{timestamp}"
            s3_key = f"{schema}/audios/raw/{audio_key}.{file_extension}"
            s3_url = f"s3://{AWS_S3_BUCKET}/{s3_key}"

            logger.info(f"Saving {audio_type} audio file with key: {audio_key}")

            # Use schema connection from pool
            with db.get_schema_connection(schema) as conn:
                with conn.cursor() as cur:
                    # Insert record using user schema
                    query = f"""
                        INSERT INTO {schema}.audios (audio_key, user_id, s3_object_url, audio_type, created_at)
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

                    cur.execute(query, query_params)
                    logger.info(f"Database record created for audio_key: {audio_key}")
                    conn.commit()

            # Upload to S3
            s3.upload_fileobj(audio_file.file, AWS_S3_BUCKET, s3_key)
            logger.info(f"Audio file uploaded to S3: {s3_key}")

            return {"audio_key": audio_key}

        except Exception as e:
            logger.error(f"Error saving audio: {str(e)}")
            raise HTTPException(status_code=500, detail="Error saving audio")

    # Notes Routes
    @app.route("/api/edit-note/{audio_key}", methods=["POST"])
    async def edit_note(request):
        schema = db.validate_schema(request.cookies.get("schema"))
        if not schema:
            raise HTTPException(status_code=401, detail="Not authenticated")

        try:
            audio_key = request.path_params["audio_key"]
            body = await request.json()
            note_title = body.get("note_title")
            transcript_text = body.get("transcript_text")

            if not note_title or not transcript_text:
                raise HTTPException(
                    status_code=400, detail="Title and transcript cannot be empty"
                )

            with db.get_schema_connection(schema) as conn:
                with conn.cursor() as cur:
                    # Verify note exists
                    cur.execute(
                        f"""
                        SELECT transcription 
                        FROM {schema}.transcripts 
                        WHERE audio_key = %s
                        """,
                        (audio_key,),
                    )
                    result = cur.fetchone()
                    if not result:
                        raise HTTPException(status_code=404, detail="Note not found")

                    # Update transcription
                    current_transcription = result[0] or {}
                    updated_transcription = {
                        **current_transcription,
                        "note_title": note_title,
                        "transcript_text": transcript_text,
                        "edited_at": datetime.now().isoformat(),
                    }

                    cur.execute(
                        f"""
                        UPDATE {schema}.transcripts 
                        SET transcription = %s::jsonb
                        WHERE audio_key = %s
                        """,
                        (json.dumps(updated_transcription), audio_key),
                    )

                    conn.commit()
                    logger.info(f"Updated note content for audio_key {audio_key}")

                    return JSONResponse(
                        {
                            "success": True,
                            "audio_key": audio_key,
                            "edited_at": updated_transcription["edited_at"],
                        }
                    )

        except HTTPException:
            raise
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in request body")
        except Exception as e:
            logger.error(f"Error editing note: {str(e)}")
            raise HTTPException(status_code=500, detail="Error editing note")

    @app.route("/api/delete-note/{audio_key}", methods=["POST"])
    async def delete_note(request: Request, audio_key: str):
        schema = db.validate_schema(request.cookies.get("schema"))
        if not schema:
            raise HTTPException(status_code=401, detail="Not authenticated")

        try:
            # Use schema connection from pool
            with db.get_schema_connection(schema) as conn:
                with conn.cursor() as cur:
                    # Check if note exists
                    cur.execute(
                        f"SELECT 1 FROM {schema}.audios WHERE audio_key = %s AND deleted_at IS NULL",
                        (audio_key,),
                    )

                    if not cur.fetchone():
                        raise HTTPException(status_code=404, detail="Note not found")

                    # Soft delete audio and transcript
                    cur.execute(
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

                    # Delete vector embedding
                    cur.execute(
                        f"""
                        UPDATE {schema}.note_vectors 
                        SET deleted_at = CURRENT_TIMESTAMP
                        WHERE audio_key = %s
                        """,
                        (audio_key,),
                    )

                    conn.commit()

                    logger.info(
                        f"Removed audio, transcript and vector embedding for audio_key {audio_key}."
                    )

                    return {"success": True}

        except Exception as e:
            logger.error(f"Error deleting note: {str(e)}")
            raise HTTPException(status_code=500, detail="Error deleting note")

    return app
