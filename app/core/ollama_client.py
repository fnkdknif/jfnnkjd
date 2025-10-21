"""
Ollama client for LLM inference and embeddings.
Provides a unified interface to Ollama API.
"""
import time
from typing import List, Dict, Any, Optional
import httpx
from pydantic import BaseModel

from app.core.config import get_config
from app.core.logging import get_logger

logger = get_logger("ollama")


class OllamaError(Exception):
    """Ollama API error."""
    pass


class GenerateResponse(BaseModel):
    """Response from generate endpoint."""
    response: str
    model: str
    created_at: str
    done: bool
    context: Optional[List[int]] = None
    total_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None


class EmbeddingResponse(BaseModel):
    """Response from embeddings endpoint."""
    embedding: List[float]


class OllamaClient:
    """
    Client for Ollama API.
    Handles LLM inference and text embeddings.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 60,
    ):
        """
        Initialize Ollama client.

        Args:
            base_url: Ollama API base URL (default from config)
            timeout: Request timeout in seconds
        """
        config = get_config()
        self.base_url = base_url or config.ollama.base_url
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout)

        logger.info(f"Initialized Ollama client: {self.base_url}")

    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> str:
        """
        Generate text completion.

        Args:
            prompt: Input prompt
            model: Model name (default from config)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Enable streaming (not implemented)

        Returns:
            Generated text

        Raises:
            OllamaError: If API call fails
        """
        config = get_config()
        model = model or config.ollama.llm_model

        start_time = time.time()

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        if max_tokens:
            payload["options"]["num_predict"] = max_tokens

        try:
            response = self.client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            result = GenerateResponse(**data)

            duration_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"Generated {result.eval_count or 0} tokens in {duration_ms}ms",
                model=model,
                prompt_tokens=result.prompt_eval_count or 0,
            )

            return result.response

        except httpx.HTTPError as e:
            logger.error(f"Ollama API error: {e}", model=model)
            raise OllamaError(f"Failed to generate: {e}")

    def embed(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> List[float]:
        """
        Generate text embedding.

        Args:
            text: Input text
            model: Embedding model name (default from config)

        Returns:
            Embedding vector

        Raises:
            OllamaError: If API call fails
        """
        config = get_config()
        model = model or config.ollama.embedding_model

        start_time = time.time()

        payload = {
            "model": model,
            "prompt": text,
        }

        try:
            response = self.client.post(
                f"{self.base_url}/api/embeddings",
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            result = EmbeddingResponse(**data)

            duration_ms = int((time.time() - start_time) * 1000)

            logger.debug(
                f"Generated embedding ({len(result.embedding)}D) in {duration_ms}ms",
                model=model,
            )

            return result.embedding

        except httpx.HTTPError as e:
            logger.error(f"Ollama embedding error: {e}", model=model)
            raise OllamaError(f"Failed to embed: {e}")

    def embed_batch(
        self,
        texts: List[str],
        model: Optional[str] = None,
        batch_size: int = 10,
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts
            model: Embedding model name
            batch_size: Batch size (currently processes one at a time)

        Returns:
            List of embedding vectors
        """
        embeddings = []

        for text in texts:
            embedding = self.embed(text, model=model)
            embeddings.append(embedding)

        return embeddings

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Chat completion (if model supports it).

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name
            temperature: Sampling temperature

        Returns:
            Assistant response
        """
        config = get_config()
        model = model or config.ollama.llm_model

        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }

        try:
            response = self.client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()

            data = response.json()
            return data["message"]["content"]

        except httpx.HTTPError as e:
            logger.error(f"Ollama chat error: {e}", model=model)
            raise OllamaError(f"Failed to chat: {e}")

    def check_model(self, model: str) -> bool:
        """
        Check if model is available.

        Args:
            model: Model name

        Returns:
            True if model exists
        """
        try:
            response = self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()

            data = response.json()
            models = [m["name"] for m in data.get("models", [])]

            return model in models

        except httpx.HTTPError:
            return False

    def close(self):
        """Close HTTP client."""
        self.client.close()


# Global client instance
_ollama_client: Optional[OllamaClient] = None


def get_ollama_client() -> OllamaClient:
    """Get global Ollama client instance."""
    global _ollama_client
    if _ollama_client is None:
        _ollama_client = OllamaClient()
    return _ollama_client
