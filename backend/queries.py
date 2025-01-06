"""
Database operations and schema management for Voice2Note.

This module handles all database-related operations including:
- Schema creation and validation
- SQL queries for notes and chats
- Database connection management
- Table creation and indexing

The module uses PostgreSQL for data storage and follows a multi-schema
architecture where each user gets their own schema for isolation.
"""


def get_notes(schema: str) -> str:
    """
    Generate SQL query to fetch all notes and chats for a user.

    Creates a unified view combining:
    - Audio notes with their transcriptions and metadata
    - Chat conversations with message previews

    Results are formatted consistently for display in the notes list,
    with common fields like title, preview text, and duration/message count.

    Args:
        schema (str): User's schema name

    Returns:
        str: SQL query string that returns:
            - content_type: 'note' or 'chat'
            - content_id: audio_key or chat_id
            - created_date: formatted date
            - title: note title or chat title
            - preview: transcript summary or first message
            - duration: audio duration or message count
            - sort_date: for ordering
    """
    return f"""
        WITH unified_content AS (
        -- Audio notes
        SELECT 
            'note' as content_type,
            audios.audio_key as content_id,
            TO_CHAR(audios.created_at, 'MM/DD') as created_date,
            COALESCE(transcription->>'note_title','Transcribing note...') as title,
            COALESCE(transcription->>'summary_text','Your audio is being transcribed. It will show up in here when is finished.') as preview,
            CASE 
                WHEN metadata->>'duration' is null or metadata->>'duration' = 'N/A' 
                THEN '...' 
                ELSE COALESCE(concat(split_part(metadata->>'duration',':',2), 'm ', 
                             split_part(split_part(metadata->>'duration',':',3),'.',1) , 's') , '...') 
            END as duration,
            audios.created_at as sort_date
        FROM {schema}.audios
        LEFT JOIN {schema}.transcripts ON audios.audio_key = transcripts.audio_key
        WHERE audios.deleted_at IS NULL

        UNION ALL

        -- Chat conversations
        SELECT 
            'chat' as content_type,
            chats.chat_id as content_id,
            TO_CHAR(chats.created_at, 'MM/DD') as created_date,
            title,
            COALESCE(
                (SELECT content 
                FROM {schema}.chat_messages 
                WHERE chat_messages.chat_id = chats.chat_id 
                ORDER BY created_at ASC 
                LIMIT 1),
                'Start of conversation'
            ) as preview,
            COUNT(chat_messages.message_id)::text || ' messages' as duration,
            chats.created_at as sort_date
        FROM {schema}.chats
        LEFT JOIN {schema}.chat_messages ON chats.chat_id = chat_messages.chat_id
        WHERE chats.deleted_at IS NULL
        GROUP BY chats.chat_id, chats.title, chats.created_at
        )
        SELECT * FROM unified_content
    """


def get_note_detail(schema: str) -> str:
    """
    Generate SQL query to fetch details of a specific note.

    Retrieves complete note information including:
    - Audio metadata
    - Transcription content
    - Note title
    - Creation date

    Args:
        schema (str): User's schema name

    Returns:
        str: SQL query string that expects an audio_key parameter and returns:
            - audio_key: Unique identifier
            - note_date: Formatted creation date
            - note_title: Title from transcription
            - note_transcription: Full transcription text
    """
    return f"""
        SELECT 
            audios.audio_key,
            TO_CHAR(audios.created_at, 'MM/DD') as note_date,
            COALESCE(transcription->>'note_title','Transcribing note...') as note_title,
            COALESCE(transcription->>'transcript_text','Your audio is being transcribed...') as note_transcription
        FROM {schema}.audios
        LEFT JOIN {schema}.transcripts ON audios.audio_key = transcripts.audio_key
        WHERE audios.audio_key = %s
        AND audios.deleted_at IS NULL
    """
