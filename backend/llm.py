"""
Language model integration for Voice2Note.

This module handles all interactions with OpenAI's GPT models, including:
- Chat completions for conversational AI
- Text embeddings for semantic search
- Rate limiting for API calls
- Chat title generation

The module uses OpenAI's API and includes rate limiting to prevent abuse.
"""

import openai
import numpy as np
import json
from typing import List, Tuple
from backend.config import logger, OPENAI_API_KEY
from collections import defaultdict
from time import time


class LLM:
    """
    Language Model interface for Voice2Note.

    Handles all interactions with OpenAI's models including chat completions,
    embeddings generation, and semantic search functionality. Includes rate
    limiting to prevent API abuse.

    Attributes:
        rate_limiter (RateLimiter): Rate limiting utility for API calls
    """

    def __init__(self):
        """Initialize LLM with API key and rate limiter."""
        openai.api_key = OPENAI_API_KEY
        self.rate_limiter = RateLimiter()

    def get_chat_completion(
        self, messages: List[dict], temperature: float = 0.7
    ) -> str:
        """
        Get completion from OpenAI's chat model.

        Args:
            messages (List[dict]): List of message objects with 'role' and 'content'
            temperature (float, optional): Temperature for response generation. Defaults to 0.7

        Returns:
            str: Generated response text

        Raises:
            Exception: If OpenAI API call fails
        """
        try:
            chat_completion = openai.chat.completions.create(
                model="gpt-4",
                messages=messages,
                temperature=temperature,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Error getting chat completion: {str(e)}")
            raise

    def find_relevant_context(
        self, schema: str, cursor, query: str, limit: int = 3
    ) -> List[Tuple[str, str, float]]:
        """
        Find relevant context from user's notes using semantic search.

        Uses OpenAI's embedding model to find semantically similar content
        from the user's notes database.

        Args:
            schema (str): User's database schema
            cursor: Database cursor for executing queries
            query (str): Search query text
            limit (int, optional): Maximum number of results. Defaults to 3

        Returns:
            List[Tuple[str, str, float]]: List of (content, audio_key, similarity_score)

        Raises:
            Exception: If embedding generation or database query fails
        """
        try:
            query_embedding = (
                openai.embeddings.create(model="text-embedding-ada-002", input=query)
                .data[0]
                .embedding
            )

            cursor.execute(
                f"""
                SELECT content_chunk, audio_key, embedding 
                FROM {schema}.note_vectors 
                WHERE deleted_at IS NULL
                """
            )
            chunks = cursor.fetchall()

            similarities = []
            for chunk in chunks:
                try:
                    embedding = (
                        json.loads(chunk[2]) if isinstance(chunk[2], str) else chunk[2]
                    )
                    similarities.append(
                        (
                            chunk[0],  # content
                            chunk[1],  # audio_key
                            self._cosine_similarity(
                                query_embedding, embedding
                            ),  # similarity
                        )
                    )
                except Exception as e:
                    logger.error(f"Error processing chunk embedding: {str(e)}")

            return sorted(similarities, key=lambda x: x[2], reverse=True)[:limit]

        except Exception as e:
            logger.error(f"Error finding relevant context: {str(e)}")
            raise

    def generate_chat_title(self, messages: List[dict]) -> str:
        """
        Generate a descriptive title for a chat based on its messages.

        Args:
            messages (List[dict]): First few messages of the chat

        Returns:
            str: Generated title (max 40 chars)

        Raises:
            Exception: If title generation fails
        """
        try:
            prompt = f"""Based on these chat messages, generate a short, descriptive title without using quotation marks (max 40 chars):

            {' '.join([m['content'] for m in messages[:3]])}

            Generate only the title, nothing else."""

            return self.get_chat_completion(
                [
                    {
                        "role": "system",
                        "content": "You generate short, descriptive chat titles in no more than 3 words.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )
        except Exception as e:
            logger.error(f"Error generating chat title: {str(e)}")
            raise

    def is_allowed(self, user_id: str) -> bool:
        """
        Check if user is allowed to make API requests.

        Args:
            user_id (str): User identifier

        Returns:
            bool: True if request is allowed, False if rate limited
        """
        return self.rate_limiter.is_allowed(user_id)

    def _cosine_similarity(self, vector_a: list, vector_b: list) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vector_a (list): First vector
            vector_b (list): Second vector

        Returns:
            float: Similarity score between 0 and 1

        Raises:
            Exception: If vector calculation fails
        """
        try:
            a = np.array(vector_a)
            b = np.array(vector_b)
            return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
        except Exception as e:
            logger.error(f"Error calculating similarity: {str(e)}")
            raise


class RateLimiter:
    """
    Rate limiting utility to prevent API abuse.

    Implements a sliding window rate limiter that tracks requests
    per user within a specified time window.

    Attributes:
        max_requests (int): Maximum allowed requests per window
        window (int): Time window in seconds
        requests (defaultdict): Tracks request timestamps per user
    """

    def __init__(self, max_requests=5, window=60):  # 5 requests per minute
        """
        Initialize rate limiter.

        Args:
            max_requests (int, optional): Max requests per window. Defaults to 5
            window (int, optional): Window size in seconds. Defaults to 60
        """
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)

    def is_allowed(self, user_id) -> bool:
        """
        Check if a request is allowed for the given user.

        Removes expired timestamps and checks if new request would exceed limit.

        Args:
            user_id: User identifier

        Returns:
            bool: True if request is allowed, False otherwise
        """
        now = time()
        user_requests = self.requests[user_id]
        user_requests[:] = [req for req in user_requests if now - req < self.window]

        if len(user_requests) >= self.max_requests:
            return False

        user_requests.append(now)
        return True
