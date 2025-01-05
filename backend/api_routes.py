from fasthtml.common import *
from datetime import datetime
from starlette.responses import JSONResponse, RedirectResponse, StreamingResponse
from starlette.exceptions import HTTPException
import bcrypt
import uuid
from datetime import datetime, timedelta
from frontend.styles import Styles
from backend.config import conn, logger, s3, AWS_S3_BUCKET
from backend.queries import validate_schema, create_user_schema
from backend.llm import (
    RateLimiter,
    get_chat_completion,
    find_relevant_context,
    generate_chat_title,
)
import json
import io

# Initialize shared resources
cursor = conn.cursor()
rate_limiter = RateLimiter(max_requests=5, window=60)

# Initialize styles
styles = Styles()


def setup_api_routes(app):
    """
    Add API routes to the main application.

    This function takes the main FastHTML app instance and adds all API routes to it.
    Each route is added using app.route() with appropriate HTTP methods.

    Args:
        app: The FastHTML application instance

    Returns:
        The app instance with routes added
    """

    # Authentication Routes
    @app.route("/api/login", methods=["POST"])
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
            # Verify password
            if not bcrypt.checkpw(password.encode("utf-8"), user[2].encode("utf-8")):
                return Html(
                    Head(
                        Meta(
                            name="viewport",
                            content="width=device-width, initial-scale=1.0",
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
            logger.error(f"Error in login: {str(e)}")
            conn.rollback()
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
                        P("An error occurred. Please try again.", cls="error-message"),
                        A("Try Again", href="/login", cls="auth-btn"),
                        cls="auth-container",
                    )
                ),
            )

    @app.route("/api/signup", methods=["POST"])
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
                    Meta(
                        name="viewport", content="width=device-width, initial-scale=1.0"
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
                value=f"user_{user_id}",
                httponly=True,
                max_age=7 * 24 * 60 * 60,
                secure=True,
                samesite="lax",
            )
            return response

        except Exception as e:
            conn.rollback()
            logger.error(f"Error in signup process: {str(e)}", exc_info=True)
            logger.error(f"Error in signup: {str(e)}")
            return Html(
                Head(
                    Meta(
                        name="viewport", content="width=device-width, initial-scale=1.0"
                    ),
                    Title("Sign Up Error - Voice2Note"),
                    Style(styles.common()),
                ),
                Body(
                    Div(
                        H1("Sign Up Error", cls="auth-title"),
                        P(
                            "Error creating account. Please try again.",
                            cls="error-message",
                        ),
                        A("Try Again", href="/signup", cls="auth-btn"),
                        cls="auth-container",
                    )
                ),
            )

    @app.route("/api/logout", methods=["POST"])
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

    @app.route("/api/request-reset", methods=["POST"])
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

    @app.route("/api/delete-chat/{chat_id}", methods=["POST"])
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

    @app.route("/api/chat/{chat_id}/messages")
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

    @app.route("/api/edit-chat-title/{chat_id}", methods=["POST"])
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

    # Audio Routes
    @app.route("/api/get-audio/{audio_key}", methods=["GET"])
    async def get_audio(request):
        """Stream audio file from S3."""
        schema = validate_schema(request.cookies.get("schema"))
        if not schema:
            raise HTTPException(status_code=401, detail="Not authenticated")

        try:
            audio_key = request.path_params["audio_key"]

            # Get audio URL from database
            cursor.execute(
                f"""
                SELECT metadata->>'s3_compressed_audio_url'
                FROM {schema}.audios 
                WHERE audio_key = %s 
                AND deleted_at IS NULL
                """,
                (audio_key,),
            )
            result = cursor.fetchone()

            if not result or not result[0]:
                raise HTTPException(status_code=404, detail="Audio not found")

            s3_url = result[0]
            if not s3_url.startswith("s3://"):
                raise ValueError("Invalid S3 URI format")

            # Extract key from s3:// URI
            s3_key = s3_url.replace(f"s3://{AWS_S3_BUCKET}/", "")

            # Get file from S3
            try:
                response = s3.get_object(Bucket=AWS_S3_BUCKET, Key=s3_key)
                audio_data = response["Body"].read()

                return StreamingResponse(
                    io.BytesIO(audio_data),
                    media_type="audio/webm",
                    headers={"Accept-Ranges": "bytes"},
                )

            except Exception as e:
                logger.error(f"S3 error - Bucket: {AWS_S3_BUCKET}, Key: {s3_key}")
                raise HTTPException(
                    status_code=500, detail=f"Error fetching audio: {str(e)}"
                )

        except ValueError as e:
            logger.error(f"Invalid S3 URI format: {str(e)}")
            raise HTTPException(status_code=500, detail="Invalid S3 URI format")
        except Exception as e:
            logger.error(f"Error in get_audio: {str(e)}")
            raise HTTPException(status_code=500, detail="Server error")

    # Note Editing Routes
    @app.route("/api/edit-note/{audio_key}", methods=["POST"])
    async def edit_note(request):
        """Handle note content updates."""
        schema = validate_schema(request.cookies.get("schema"))
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

            # Verify note exists and belongs to user
            cursor.execute(
                f"""
                SELECT transcription 
                FROM {schema}.transcripts 
                WHERE audio_key = %s
                """,
                (audio_key,),
            )
            result = cursor.fetchone()
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
            conn.rollback()
            logger.error(f"Error editing note: {str(e)}")
            raise HTTPException(status_code=500, detail="Error editing note")

    return app
