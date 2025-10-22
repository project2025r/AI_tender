import httpx
import logging
import json
from typing import AsyncGenerator
from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.ollama_base_url
        self.model = self.settings.llm_model
    
    async def generate(self, prompt: str, stream: bool = False) -> AsyncGenerator[str, None]:
        """Generate response from Ollama"""
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": 0.7,
                "num_predict": 500  # Limit response length
            }
        }
        
        logger.info(f"Calling Ollama with model: {self.model}")
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                if stream:
                    async with client.stream("POST", url, json=payload) as response:
                        if response.status_code != 200:
                            error_text = await response.aread()
                            logger.error(f"Ollama error response: {error_text.decode()}")
                            raise httpx.HTTPStatusError(
                                f"Ollama returned status {response.status_code}: {error_text.decode()}",
                                request=response.request,
                                response=response
                            )
                        
                        async for line in response.aiter_lines():
                            if line:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                else:
                    response = await client.post(url, json=payload)
                    
                    if response.status_code != 200:
                        error_text = response.text
                        logger.error(f"Ollama error response: {error_text}")
                        logger.error(f"Requested model: {self.model}")
                        logger.error(f"Available models: Run 'ollama list' to see available models")
                        raise httpx.HTTPStatusError(
                            f"Ollama returned status {response.status_code}. Model '{self.model}' may not be available. Error: {error_text}",
                            request=response.request,
                            response=response
                        )
                    
                    result = response.json()
                    yield result.get("response", "")
        
        except httpx.HTTPError as e:
            logger.error(f"HTTP error calling Ollama: {e}")
            logger.error(f"Make sure the model '{self.model}' is installed. Run: ollama list")
            raise
        except Exception as e:
            logger.error(f"Error calling Ollama: {e}")
            raise
    
    async def check_health(self) -> bool:
        """Check if Ollama is accessible"""
        try:
            url = f"{self.base_url}/api/tags"
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return True
        except:
            return False


def get_llm_service() -> LLMService:
    """Get LLM service instance"""
    return LLMService()

