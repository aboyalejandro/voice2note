import openai
import numpy as np
import json
from typing import List, Tuple
from backend.config import logger
from backend.config import OPENAI_API_KEY
from collections import defaultdict
from time import time

openai.api_key = OPENAI_API_KEY


class RateLimiter:
    def __init__(self, max_requests=5, window=60):  # 5 requests per minute
        self.max_requests = max_requests
        self.window = window
        self.requests = defaultdict(list)

    def is_allowed(self, user_id):
        now = time()
        user_requests = self.requests[user_id]
        user_requests[:] = [req for req in user_requests if now - req < self.window]

        if len(user_requests) >= self.max_requests:
            return False

        user_requests.append(now)
        return True


def get_chat_completion(messages: List[dict], temperature: float = 0.7) -> str:
    """Get chat completion from OpenAI.

    Args:
        messages (List[dict]): List of message objects with 'role' and 'content'
        temperature (float): Temperature for response generation

    Returns:
        str: Generated response

    Raises:
        Exception: If OpenAI API call fails
    """
    try:
        chat_completion = openai.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            temperature=temperature,
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        logger.error(f"Error getting chat completion: {str(e)}")
        raise


def find_relevant_context(
    schema: str, cursor, query: str, limit: int = 3
) -> List[Tuple[str, str, float]]:
    try:
        # Get embedding for query
        query_embedding = (
            openai.embeddings.create(model="text-embedding-ada-002", input=query)
            .data[0]
            .embedding
        )

        # Get all vectors from database
        cursor.execute(
            f"""
            SELECT content_chunk, audio_key, embedding 
            FROM {schema}.note_vectors 
            WHERE deleted_at IS NULL
            """
        )
        chunks = cursor.fetchall()

        # Calculate similarities
        similarities = []
        for chunk in chunks:
            try:
                embedding = (
                    json.loads(chunk[2]) if isinstance(chunk[2], str) else chunk[2]
                )  # Ensure the embedding is a list
                similarities.append(
                    (
                        chunk[0],  # content
                        chunk[1],  # audio_key
                        cosine_similarity(query_embedding, embedding),  # similarity
                    )
                )
            except Exception as e:
                logger.error(f"Error processing chunk embedding: {str(e)}")

        # Return top matches
        return sorted(similarities, key=lambda x: x[2], reverse=True)[:limit]

    except Exception as e:
        logger.error(f"Error finding relevant context: {str(e)}")
        raise


def cosine_similarity(vector_a: list, vector_b: list) -> float:
    """Calculate cosine similarity between two vectors."""
    try:
        a = np.array(vector_a)
        b = np.array(vector_b)
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    except Exception as e:
        logger.error(f"Error calculating similarity: {str(e)}")
        raise


def generate_chat_title(messages: List[dict]) -> str:
    """Generate a title for a chat based on initial messages.

    Args:
        messages (List[dict]): First few messages of the chat

    Returns:
        str: Generated title
    """
    try:
        prompt = f"""Based on these chat messages, generate a short, descriptive title (max 40 chars):

        {' '.join([m['content'] for m in messages[:3]])}

        Generate only the title, nothing else."""

        return get_chat_completion(
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
