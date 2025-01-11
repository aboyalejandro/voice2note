"""
Database management for Voice2Note.
Handles connections, schema creation, and user management.
"""

from backend.config import logger
from contextlib import contextmanager
from typing import Optional, Tuple, Dict
import psycopg2
from psycopg2.extensions import connection
import bcrypt
import os


class DatabaseManager:
    def __init__(self, db_config):
        self.db_config = db_config

    def ensure_app_pool(self):
        """Ensure app pool exists, create if it doesn't"""
        if not self.db_config.app_pool:
            self.db_config.app_pool = self.db_config._create_app_pool()

    def ensure_user_pool(self, user_id: int):
        """Ensure user pool exists, create if it doesn't"""
        pool_key = f"user_{user_id}"
        if pool_key not in self.db_config.user_pools:
            # Get user's password from database
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT hashed_password FROM public.users WHERE user_id = %s",
                        (user_id,),
                    )
                    hashed_password = cur.fetchone()[0]
                    self.db_config.create_user_pool(user_id, hashed_password)

    @staticmethod
    def validate_schema(schema: str) -> Optional[str]:
        """
        Validate schema name format.
        Returns None if schema is invalid or missing.
        """
        if not schema or not isinstance(schema, str):
            return None

        try:
            if (
                not schema.startswith("user_")
                or not schema.replace("user_", "").isdigit()
            ):
                return None
            return schema
        except Exception:
            return None

    @staticmethod
    def get_schema_id(schema: str) -> Optional[int]:
        """Extract user ID from schema name"""
        try:
            schema = DatabaseManager.validate_schema(schema)
            if not schema:
                return None
            return int(schema.replace("user_", ""))
        except Exception:
            return None

    @contextmanager
    def get_connection(self, user_id: Optional[int] = None):
        """Get database connection from appropriate pool"""
        conn = None
        try:
            if user_id:
                self.ensure_user_pool(user_id)
                conn = self.db_config.get_user_connection(user_id)
            else:
                self.ensure_app_pool()
                conn = self.db_config.get_app_connection()
            yield conn
        finally:
            if conn:
                if user_id:
                    self.db_config.return_user_connection(user_id, conn)
                else:
                    self.db_config.return_app_connection(conn)

    @contextmanager
    def get_schema_connection(self, schema: str):
        """Get connection for a specific schema"""
        if not schema:
            raise HTTPException(status_code=401, detail="Not authenticated")
        user_id = self.get_schema_id(schema)
        with self.get_connection(user_id) as conn:
            yield conn

    def verify_user_credentials(
        self, username: str, password: str
    ) -> Tuple[bool, Optional[int]]:
        """Verify user login credentials"""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT user_id, hashed_password FROM public.users WHERE username = %s",
                    (username,),
                )
                result = cur.fetchone()

                if not result:
                    return False, None

                user_id, hashed_password = result

                if bcrypt.checkpw(
                    password.encode("utf-8"), hashed_password.encode("utf-8")
                ):
                    return True, user_id

                return False, None

    def create_schema_tables(self, cur, schema: str):
        """Create required tables in user schema"""
        cur.execute(
            f"""
            CREATE TABLE {schema}.audios (
                audio_id SERIAL NOT NULL,
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

        cur.execute(
            f"""
            CREATE TABLE {schema}.transcripts (
                transcript_id SERIAL NOT NULL,
                audio_key varchar(255) NOT NULL,
                s3_object_url text NULL,
                transcription jsonb NULL,
                created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
                deleted_at timestamp NULL,
                CONSTRAINT transcripts_pkey PRIMARY KEY (transcript_id)
            )
        """
        )

        cur.execute(
            f"""
            CREATE TABLE {schema}.chats (
                chat_id varchar(255) NOT NULL,
                title varchar(255) NOT NULL,
                created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
                deleted_at timestamp NULL,
                CONSTRAINT chats_pkey PRIMARY KEY (chat_id)
            )
        """
        )

        cur.execute(
            f"""
            CREATE TABLE {schema}.chat_messages (
                message_id SERIAL NOT NULL,
                chat_id varchar(255) NOT NULL,
                role varchar(10) NOT NULL,
                content text NOT NULL,
                source_refs jsonb NULL,
                created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
                CONSTRAINT chat_messages_pkey PRIMARY KEY (message_id),
                CONSTRAINT chat_messages_role_check CHECK (role IN ('user', 'assistant')),
                CONSTRAINT chat_messages_chat_id_fkey FOREIGN KEY (chat_id) 
                    REFERENCES {schema}.chats(chat_id)
            )
        """
        )

        cur.execute(
            f"""
            CREATE TABLE {schema}.note_vectors (
                vector_id SERIAL NOT NULL,
                audio_key varchar(255) NOT NULL,
                content_chunk text NOT NULL,
                embedding jsonb NOT NULL,
                created_at timestamp DEFAULT CURRENT_TIMESTAMP NOT NULL,
                deleted_at timestamp NULL,
                CONSTRAINT note_vectors_pkey PRIMARY KEY (vector_id),
                CONSTRAINT note_vectors_audio_key_fkey FOREIGN KEY (audio_key) 
                    REFERENCES {schema}.audios(audio_key)
            )
        """
        )

    def create_user_schema(self, user_id: int) -> bool:
        """Create new schema, tables, and privileges for a user."""
        logger.info(f"Starting schema creation for user_id: {user_id}")

        with self.get_connection() as conn:
            conn.autocommit = True
            try:
                with conn.cursor() as cur:
                    schema_name = f"user_{user_id}"

                    # Step 1: Create schema
                    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

                    # Step 2: Fetch hashed password for the user
                    cur.execute(
                        "SELECT hashed_password FROM public.users WHERE user_id = %s",
                        (user_id,),
                    )
                    result = cur.fetchone()
                    if not result or not result[0]:
                        raise ValueError(
                            f"No hashed_password found for user_id: {user_id}"
                        )

                    hashed_password = result[0]

                    # Step 3: Create database user for the schema
                    cur.execute(
                        f"CREATE USER {schema_name} WITH PASSWORD %s",
                        (hashed_password,),
                    )

                    # Step 4: Grant role_user_schema to the new user and schema privileges
                    cur.execute(
                        f"""
                        GRANT role_user_schema TO {schema_name};
                        GRANT USAGE ON SCHEMA {schema_name} TO {schema_name};
                    """
                    )

                    # Step 5: Create all required tables in the schema
                    self.create_schema_tables(cur, schema_name)

                    # Step 6: Set replica identity for CDC tracking
                    cur.execute(
                        f"""
                        ALTER TABLE {schema_name}.audios REPLICA IDENTITY DEFAULT;
                        ALTER TABLE {schema_name}.transcripts REPLICA IDENTITY DEFAULT;
                        ALTER TABLE {schema_name}.chats REPLICA IDENTITY DEFAULT;
                        ALTER TABLE {schema_name}.chat_messages REPLICA IDENTITY DEFAULT;
                        ALTER TABLE {schema_name}.note_vectors REPLICA IDENTITY DEFAULT;
                        """
                    )

                    # Step 7: Grant privileges on existing tables to schema owner
                    cur.execute(
                        f"""
                        GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA {schema_name} TO {schema_name};
                        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema_name} TO {schema_name};
                    """
                    )

                    # Step 8: Add privileges to dbt_analytics
                    cur.execute(
                        f"""
                        GRANT SELECT ON ALL TABLES IN SCHEMA {schema_name} TO dbt_analytics;
                    """
                    )

                    # Step 9: Set up default privileges for future tables
                    cur.execute(
                        f"""
                        ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_name} 
                            GRANT SELECT, INSERT, UPDATE ON TABLES TO {schema_name};
                        ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_name} 
                            GRANT USAGE, SELECT ON SEQUENCES TO {schema_name};
                    """
                    )

                    # Step 10: Grant Lambda permissions last
                    cur.execute(
                        f"""
                        GRANT USAGE ON SCHEMA {schema_name} TO aws_lambda;
                        GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA {schema_name} TO aws_lambda;
                        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema_name} TO aws_lambda;
                        ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_name} 
                            GRANT SELECT, INSERT, UPDATE ON TABLES TO aws_lambda;
                        ALTER DEFAULT PRIVILEGES IN SCHEMA {schema_name} 
                            GRANT USAGE, SELECT ON SEQUENCES TO aws_lambda;
                    """
                    )

                    # Create connection pool for this user
                    self.db_config.create_user_pool(user_id, hashed_password)

                    logger.info(
                        f"Successfully created schema and roles for user_{user_id}"
                    )
                    return True

            except Exception as e:
                logger.error(f"Error creating schema for user_{user_id}: {str(e)}")
                raise

    def handle_password_reset(self, user_id: int):
        """Update DB user password after a password reset"""
        with self.get_connection() as conn:
            try:
                with conn.cursor() as cur:
                    # Get new hashed password
                    cur.execute(
                        "SELECT hashed_password FROM public.users WHERE user_id = %s",
                        (user_id,),
                    )
                    hashed_password = cur.fetchone()[0]

                    # Update database user password
                    cur.execute(
                        f"ALTER USER user_{user_id} WITH PASSWORD %s",
                        (hashed_password,),
                    )

                    # Update the connection pool
                    self.db_config.create_user_pool(user_id, hashed_password)

                    conn.commit()
                    logger.info(f"Successfully reset password for user_{user_id}")

            except Exception as e:
                conn.rollback()
                logger.error(f"Error resetting password: {str(e)}")
                raise
