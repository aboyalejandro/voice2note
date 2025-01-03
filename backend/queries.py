from backend.config import conn, logger

cursor = conn.cursor()


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

        # Create chats table
        cursor.execute(
            f"""
            CREATE TABLE user_{user_id}.chats (
                chat_id varchar(255) NOT NULL,
                title varchar(255) NOT NULL,
                created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
                deleted_at timestamp NULL,
                CONSTRAINT chats_pkey PRIMARY KEY (chat_id)
            )
        """
        )
        logger.info(f"Chats table created for user_{user_id}")

        # Create chat_messages table
        cursor.execute(
            f"""
            CREATE TABLE user_{user_id}.chat_messages (
                message_id serial4 NOT NULL,
                chat_id varchar(255) NOT NULL,
                role varchar(10) NOT NULL,
                content text NOT NULL,
                source_refs jsonb NULL,
                created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
                CONSTRAINT chat_messages_pkey PRIMARY KEY (message_id),
                CONSTRAINT chat_messages_role_check CHECK (role IN ('user', 'assistant')),
                CONSTRAINT chat_messages_chat_id_fkey FOREIGN KEY (chat_id) 
                    REFERENCES user_{user_id}.chats(chat_id)
            )
        """
        )
        logger.info(f"Chat messages table created for user_{user_id}")

        # Create note_vectors table
        cursor.execute(
            f"""
            CREATE TABLE user_{user_id}.note_vectors (
                vector_id serial4 NOT NULL,
                audio_key varchar(255) NOT NULL,
                content_chunk text NOT NULL,
                embedding jsonb NOT NULL,
                created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
                deleted_at timestamp NULL,
                CONSTRAINT note_vectors_pkey PRIMARY KEY (vector_id),
                CONSTRAINT note_vectors_audio_key_fkey FOREIGN KEY (audio_key) 
                    REFERENCES user_{user_id}.audios(audio_key)
            )
        """
        )
        logger.info(f"Note vectors table created for user_{user_id}")

        # Create indexes
        cursor.execute(
            f"""
            CREATE INDEX idx_audios_audio_id ON user_{user_id}.audios USING btree (audio_id);
            CREATE INDEX idx_transcripts_audio_id ON user_{user_id}.transcripts USING btree (audio_key);
            CREATE INDEX idx_transcripts_transcript_id ON user_{user_id}.transcripts USING btree (transcript_id);
            CREATE INDEX idx_chats_chat_id ON user_{user_id}.chats USING btree (chat_id);
            CREATE INDEX idx_chat_messages_chat_id ON user_{user_id}.chat_messages USING btree (chat_id);
            CREATE INDEX idx_note_vectors_audio_key ON user_{user_id}.note_vectors USING btree (audio_key)
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


def validate_schema(schema):
    if not schema.startswith("user_") or not schema.replace("user_", "").isdigit():
        raise ValueError("Invalid schema")
    return schema


def get_notes(schema):
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


def get_note_detail(schema):
    return f"""
            SELECT 
                audios.audio_key,
                TO_CHAR(audios.created_at, 'MM/DD') as note_date,
                COALESCE(transcription->>'note_title','Transcribing note...') as note_title,
                COALESCE(transcription->>'transcript_text','Your audio is being transcribed. It will show up in here when is finished.') as note_transcription
            FROM {schema}.audios
            LEFT JOIN {schema}.transcripts ON audios.audio_key = transcripts.audio_key
            WHERE audios.audio_key = %s
            AND audios.deleted_at IS NULL
            """
