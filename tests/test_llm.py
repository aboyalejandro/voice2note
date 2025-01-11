import pytest
from backend.llm import LLM


@pytest.fixture
def llm():
    return LLM()


def test_rate_limiter():
    """Test rate limiting"""
    from backend.llm import RateLimiter

    limiter = RateLimiter(max_requests=2, window=1)

    # First two requests should be allowed
    assert limiter.is_allowed("test_user")
    assert limiter.is_allowed("test_user")

    # Third request should be blocked
    assert not limiter.is_allowed("test_user")


@pytest.mark.skip(reason="Requires OpenAI API key")
def test_chat_completion(llm):
    """Test chat completion"""
    messages = [{"role": "user", "content": "Hello"}]
    response = llm.get_chat_completion(messages)
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.skip(reason="Requires OpenAI API key")
def test_chat_title_generation(llm):
    """Test chat title generation"""
    messages = [
        {"role": "user", "content": "What's the weather like?"},
        {"role": "assistant", "content": "It's sunny today."},
    ]
    title = llm.generate_chat_title(messages)
    assert isinstance(title, str)
    assert len(title) <= 40
