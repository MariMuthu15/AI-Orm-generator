import os
from typing import List, Optional
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()

class AIService:
    def __init__(self, model_name: str, base_url: Optional[str] = None):
        self.model_name = model_name
        self.client = AsyncOpenAI(
            api_key=os.getenv("AI_API_KEY"),
            base_url=base_url or os.getenv("AI_API_BASE_URL"),
        )

    async def chat(self, messages: List[dict], **kwargs):
        response = await self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            max_tokens=1024,
            **kwargs,
        )
        return response.choices[0].message.content
