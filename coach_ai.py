from openai import AsyncOpenAI

from config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODEL

# Groq exposes an OpenAI-compatible API, so we reuse the openai SDK
# and just point it at Groq's base_url instead of OpenAI's.
client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)

SYSTEM_PROMPT = (
    "You are English Coach, a friendly, encouraging English tutor chatting with a "
    "language learner on Telegram. For every message the learner sends:\n"
    "1. If there are grammar, spelling, word-choice, or phrasing mistakes, gently point "
    "them out and show the corrected version.\n"
    "2. Briefly explain the fix in one short sentence (skip this if there's nothing to fix).\n"
    "3. Then continue the conversation naturally by replying to the content of their "
    "message and asking a short follow-up question to keep them talking.\n"
    "Keep your whole reply under 100 words, use simple formatting, and always stay "
    "warm and motivating. If the message is already correct, say so briefly and "
    "just continue the conversation."
)


async def get_coaching_reply(user_message: str, history: list[dict] | None = None) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-6:])  # keep last few turns for context
    messages.append({"role": "user", "content": user_message})

    response = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        max_tokens=300,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()
