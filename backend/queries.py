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

from backend.cache import QueryCache
from backend.config import REDIS_URL, logger, db_config
from backend.database import DatabaseManager

db = DatabaseManager(db_config)

# Initialize cache with 5 minute default timeout
cache = QueryCache(redis_url=REDIS_URL)


def _get_notes(schema: str) -> str:
    """Internal: Generate base SQL for notes list."""
    return f"""
        WITH unified_content AS (
        -- Audio notes
        SELECT 
            'note' as content_type,
            audios.audio_key as content_id,
            TO_CHAR(audios.created_at, 'MM/DD') as created_date,
            CASE
                WHEN transcripts.transcription IS NULL THEN 'Transcribing note...'
                WHEN transcripts.transcription->>'note_title' IS NULL THEN 'Processing title...'
                ELSE transcripts.transcription->>'note_title'
            END as title,
            CASE
                WHEN transcripts.transcription IS NULL THEN 'Your audio is being transcribed. It will show up in here when finished.'
                WHEN transcripts.transcription->>'summary_text' IS NULL THEN 'Generating summary...'
                ELSE transcripts.transcription->>'summary_text'
            END as preview,
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


def _get_note_detail(schema: str) -> str:
    """Internal: Generate base SQL for note detail."""
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


def get_notes_with_cache(schema: str, filters: dict = None) -> list:
    """Get notes list with caching support."""
    if not filters:  # Only cache when no filters are applied
        cache_key = f"notes:{schema}"
        cached_result = cache.get(cache_key)
        if cached_result is not None:
            logger.info(f"Cache hit for notes:{schema}")
            return cached_result

    # Execute query
    query = _get_notes(schema)

    # Add filters if present
    params = []
    if filters:
        conditions = []
        if filters.get("start_date"):
            conditions.append("DATE(sort_date) >= %s")
            params.append(filters["start_date"])
        if filters.get("end_date"):
            conditions.append("DATE(sort_date) <= %s")
            params.append(filters["end_date"])
        if filters.get("keyword"):
            conditions.append("(title ILIKE %s OR preview ILIKE %s)")
            params.extend([f"%{filters['keyword']}%", f"%{filters['keyword']}%"])

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY sort_date DESC"

    # Execute query and cache result if no filters
    with db.get_schema_connection(schema) as conn:
        with conn.cursor() as cur:
            cur.execute(query, params)
            result = cur.fetchall()

            if not filters:  # Only cache when no filters
                cache.set(cache_key, result)
                logger.info(f"Cached notes for {schema}")

            return result


def get_note_detail_with_cache(schema: str, audio_key: str) -> dict:
    """Get note detail with caching support."""
    cache_key = f"note:{schema}:{audio_key}"
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        logger.info(f"Cache hit for note:{schema}:{audio_key}")
        return cached_result

    # Execute query
    query = _get_note_detail(schema)
    with db.get_schema_connection(schema) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (audio_key,))
            result = cur.fetchone()
            if result:
                cache.set(cache_key, result)
                logger.info(f"Cached note detail for {audio_key}")
            return result


def invalidate_note_cache(schema: str, audio_key: str = None):
    """
    Invalidate cache when notes are modified.
    """
    # Always invalidate notes list
    cache.delete(f"notes:{schema}")
    logger.info(f"Invalidated notes cache for {schema}")

    # Invalidate specific note if provided
    if audio_key:
        cache.delete(f"note:{schema}:{audio_key}")
        logger.info(f"Invalidated note cache for {audio_key}")
