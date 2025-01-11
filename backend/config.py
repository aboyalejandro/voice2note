from psycopg2 import pool
import boto3
import os
from dotenv import load_dotenv
import logging
from typing import Dict

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s",
)
logger = logging.getLogger("voice2note")


class DatabaseConfig:
    def __init__(self):
        # App role connection pool (static credentials)
        self.app_pool = self._create_app_pool()
        # User schema pools (dynamic, created on demand)
        self.user_pools: Dict[str, pool.SimpleConnectionPool] = {}

    def _create_app_pool(self) -> pool.SimpleConnectionPool:
        """Create the main application connection pool"""
        return pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_APP_USER"),
            password=os.getenv("DB_APP_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )

    def _create_user_pool(
        self, user_id: int, db_password: str
    ) -> pool.SimpleConnectionPool:
        """
        Create a user-specific connection pool using their database user password
        Note: This is different from their login password hash
        """
        return pool.SimpleConnectionPool(
            minconn=1,
            maxconn=5,
            dbname=os.getenv("DB_NAME"),
            user=f"user_{user_id}",
            password=db_password,
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
        )

    def get_app_connection(self):
        """Get a connection from the app pool"""
        return self.app_pool.getconn()

    def create_user_pool(self, user_id: int, db_password: str):
        """Create or replace a user-specific pool"""
        pool_key = f"user_{user_id}"
        if pool_key in self.user_pools:
            self.user_pools[pool_key].closeall()
        self.user_pools[pool_key] = self._create_user_pool(user_id, db_password)

    def get_user_connection(self, user_id: int):
        """Get a connection from user-specific pool"""
        pool_key = f"user_{user_id}"
        if pool_key not in self.user_pools:
            raise ValueError(f"No pool exists for user_{user_id}")
        return self.user_pools[pool_key].getconn()

    def return_app_connection(self, conn):
        """Return a connection to the app pool"""
        self.app_pool.putconn(conn)

    def return_user_connection(self, user_id: int, conn):
        """Return a connection to the user-specific pool"""
        pool_key = f"user_{user_id}"
        if pool_key in self.user_pools:
            self.user_pools[pool_key].putconn(conn)

    def close_all(self):
        """Close all connection pools"""
        self.app_pool.closeall()
        for user_pool in self.user_pools.values():
            user_pool.closeall()


# Initialize the database configuration
db_config = DatabaseConfig()

# AWS S3 Configuration
s3 = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET")

# LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Redis
REDIS_URL = os.getenv("REDIS_URL")
