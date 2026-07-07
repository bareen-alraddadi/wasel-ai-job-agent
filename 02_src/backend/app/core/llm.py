"""
Wasel — LLM Client with Fallback Chain
Primary   : OpenAI GPT-4o-mini
Fallback 1: Groq  Llama-3.3-70b-versatile
Fallback 2: DeepSeek deepseek-chat

All providers expose an OpenAI-compatible Chat Completions API,
so we can reuse the same AsyncOpenAI client with a custom base_url.
"""
import logging
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Provider definitions (in priority order) ─────────────────

_PROVIDERS: list[dict] = [
    {
        "name": "OpenAI (gpt-4o-mini)",
        "model": settings.LLM_MODEL,
        "api_key": settings.OPENAI_API_KEY,
        "base_url": None,                               # default OpenAI endpoint
    },
    {
        "name": "Groq (llama-3.3-70b)",
        "model": "llama-3.3-70b-versatile",
        "api_key": settings.GROQ_API_KEY,
        "base_url": "https://api.groq.com/openai/v1",
    },
    {
        "name": "DeepSeek (deepseek-chat)",
        "model": "deepseek-chat",
        "api_key": settings.DEEPSEEK_API_KEY,
        "base_url": "https://api.deepseek.com/v1",
    },
]


def _build_client(provider: dict) -> AsyncOpenAI | None:
    """Build an AsyncOpenAI-compatible client for a provider."""
    if not provider["api_key"]:
        return None
    kwargs = {"api_key": provider["api_key"]}
    if provider["base_url"]:
        kwargs["base_url"] = provider["base_url"]
    return AsyncOpenAI(**kwargs)


# ── Public chat_complete with auto-fallback ───────────────────

async def chat_complete(
    messages: list[dict],
    system: str = "",
    max_tokens: int = 800,
    temperature: float = 0.3,
    json_mode: bool = False,
) -> str:
    """
    Send a chat completion request with automatic fallback.

    Tries providers in order:
      1. OpenAI GPT-4o-mini
      2. Groq  Llama-3.3-70b
      3. DeepSeek deepseek-chat

    Falls back to the next provider only on connection/API errors.
    Raises RuntimeError if all providers fail.
    """
    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    last_error: Exception | None = None

    for provider in _PROVIDERS:
        client = _build_client(provider)
        if client is None:
            logger.debug(f"Skipping {provider['name']} — no API key configured.")
            continue

        try:
            kwargs = dict(
                model=provider["model"],
                messages=full_messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            # DeepSeek doesn't support json_object response_format — skip it
            if json_mode and "deepseek" not in provider["model"]:
                kwargs["response_format"] = {"type": "json_object"}

            response = await client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content or ""

            if provider["name"] != "OpenAI (gpt-4o-mini)":
                logger.info(f"✅ LLM fallback used: {provider['name']}")

            return content

        except Exception as e:
            logger.warning(
                f"⚠️  {provider['name']} failed: {type(e).__name__}: {e}. "
                f"Trying next provider…"
            )
            last_error = e
            continue

    raise RuntimeError(
        f"All LLM providers failed. Last error: {last_error}"
    )


# ── Legacy helper (kept for backwards compatibility) ──────────

def get_llm() -> AsyncOpenAI:
    """Return the primary OpenAI client (for direct use in LangChain agents)."""
    return AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
