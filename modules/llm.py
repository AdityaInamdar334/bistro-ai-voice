import os
import asyncio
from openai import AsyncOpenAI
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self, model="meta/llama-3.1-8b-instruct"):
        self.model = model
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            logger.warning("NVIDIA_API_KEY environment variable is not set!")
        
        self.client = AsyncOpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key or "no-key"
        )
        logger.info(f"LLM Service initialized for Nvidia API (model: {self.model})")

    async def generate_response_stream(self, system_prompt: str, user_input: str, conversation_history: list):
        """
        Generates a streaming response token by token.
        conversation_history: list of dicts [{"role": "user"/"assistant", "content": "..."}]
        """
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(conversation_history)
        messages.append({"role": "user", "content": user_input})
        
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5,
                top_p=1,
                max_tokens=256,
                stream=True
            )
            
            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content is not None:
                        yield delta.content
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            yield "Sorry, I encountered an error generating the response."
