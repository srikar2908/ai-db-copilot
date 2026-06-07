from groq import AsyncGroq

from app.config import settings


client = AsyncGroq(
    api_key=settings.GROQ_API_KEY
)
