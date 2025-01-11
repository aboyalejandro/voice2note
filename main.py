"""
Main application module for Voice2Note.

This module serves as the core of the Voice2Note application, providing:
- Route definitions for web pages and views
- HTML template generation using FastHTML
- Authentication and session management
- Audio recording and upload functionality
- Note management and viewing
- Chat interface and interactions

The application architecture:
- Frontend: FastHTML for templating
- Backend: PostgreSQL for data storage
- Storage: AWS S3 for audio files
- AI: OpenAI for transcription and chat
"""

from fasthtml.common import *
from backend.config import db_config
from backend.database import DatabaseManager
from backend.queries import (
    get_notes_with_cache,
    get_note_detail_with_cache,
)
from backend.api_routes import setup_api_routes
from frontend.styles import Styles
from frontend.scripts import Scripts

# Initialize database manager
db = DatabaseManager(db_config)

# Initialize frontend components
scripts = Scripts()
styles = Styles()

# Initialize FastHTML app
app, rt = fast_app()
app = setup_api_routes(app, db)


# Authentication Routes


@rt("/login")
def login(request: Request):
    """
    Render login page.

    Displays login form with username/password fields
    and links to signup and password reset.

    Args:
        request (Request): The incoming request

    Returns:
        Html: Login page template
    """
    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Login - Voice2Note"),
            Link(
                rel="stylesheet",
                href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css",
            ),
            Style(styles.common()),
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
    """
    Render signup page.

    Displays registration form for new users with
    username and password fields.

    Args:
        request (Request): The incoming request

    Returns:
        Html: Signup page template
    """
    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Sign Up - Voice2Note"),
            Link(
                rel="stylesheet",
                href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css",
            ),
            Style(styles.common()),
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


@rt("/forgot-password")
def forgot_password():
    """
    Render password reset request page.

    Displays form to request password reset by entering username.
    Reset link will be displayed (email functionality pending).

    Returns:
        Html: Password reset request page
    """
    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Reset Password - Voice2Note"),
            Style(styles.common()),
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
    """
    Render password reset page.

    Displays form to set new password after clicking reset link.

    Args:
        token (str): Password reset token from email

    Returns:
        Html: Password reset page template
    """
    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Set New Password - Voice2Note"),
            Style(styles.common()),
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


# Main App Routes


@rt("/")
def home(request):
    """
    Render home page with recording interface.

    Features:
    - Audio recording controls
    - File upload option
    - Audio playback
    - Save functionality
    - Navigation to notes

    Args:
        request (Request): The incoming request

    Returns:
        Html: Home page template
        RedirectResponse: To login if not authenticated
    """
    schema = db.validate_schema(request.cookies.get("schema"))
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
                        I(cls="fas fa-robot"),
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
                Style(styles.home()),
                Script(scripts.home()),
            ),
        ),
    )


## Notes


@rt("/notes")
def notes(request, start_date: str = None, end_date: str = None, keyword: str = None):
    """
    Render notes list page with search and filtering.

    Features:
    - List of audio notes and chats
    - Date range filtering
    - Keyword search
    - Note previews and metadata

    Args:
        request (Request): The incoming request
        start_date (str, optional): Filter notes from this date
        end_date (str, optional): Filter notes until this date
        keyword (str, optional): Search in titles and content

    Returns:
        Html: Notes list page template
        RedirectResponse: To login if not authenticated
    """
    schema = db.validate_schema(request.cookies.get("schema"))
    if not schema:
        return RedirectResponse(url="/login", status_code=303)

    # Use cached query with filters
    filters = {}
    if start_date:
        filters["start_date"] = start_date
    if end_date:
        filters["end_date"] = end_date
    if keyword:
        filters["keyword"] = keyword

    items = get_notes_with_cache(schema, filters)

    # Create search form with original styling
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
                        item[5],  # duration or message count if chat
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
            P(item[4], cls="note-preview"),  # summary
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
            Style(styles.notes()),
            Script(scripts.notes()),
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
    """
    Render note detail page.

    Features:
    - Note title and metadata
    - Audio playback
    - Transcription display
    - Edit functionality
    - Delete option

    Args:
        request (Request): The incoming request
        audio_key (str): Unique identifier for the note

    Returns:
        Html: Note detail page template
        RedirectResponse: To login if not authenticated
        HTTPException: If note not found
    """
    schema = db.validate_schema(request.cookies.get("schema"))
    if not schema:
        return RedirectResponse(url="/login", status_code=303)

    # Use cached query
    note = get_note_detail_with_cache(schema, audio_key)
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
            Style(styles.note_detail()),
            Script(scripts.note_detail()),
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


## Chat


@rt("/chat_{chat_id}")
def chat_detail(request: Request, chat_id: str):
    """
    Render chat detail page.

    Features:
    - Chat history display
    - Message input
    - Title editing
    - Delete chat option
    - Source references

    Args:
        request (Request): The incoming request
        chat_id (str): Unique identifier for the chat

    Returns:
        Html: Chat detail page template
        RedirectResponse: To login if not authenticated
    """
    schema = db.validate_schema(request.cookies.get("schema"))
    if not schema:
        return RedirectResponse(url="/login", status_code=303)

    # Use schema connection from pool
    with db.get_schema_connection(schema) as conn:
        with conn.cursor() as cur:
            # Get chat details
            cur.execute(
                f"""
                SELECT chat_id, title, created_at 
                FROM {schema}.chats 
                WHERE chat_id = %s AND deleted_at IS NULL
                """,
                (chat_id,),
            )
            chat = cur.fetchone()

            messages = []
            if chat:
                cur.execute(
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
                messages = cur.fetchall()

    return Html(
        Head(
            Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
            Title("Chat - Voice2Note"),
            Link(
                rel="stylesheet",
                href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css",
            ),
            Style(styles.chat_detail()),
        ),
        Script(scripts.chat_detail()),
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


port = int(os.environ.get("PORT", 5000))
serve(port=port, host="0.0.0.0")
