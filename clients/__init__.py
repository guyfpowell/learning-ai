import os

from clients.base import BaseModelClient


def get_model_client() -> BaseModelClient:
    provider = os.getenv("AI_PROVIDER", "ollama")
    if provider == "vertex":
        from clients.vertex_client import VertexClient
        return VertexClient()
    from clients.ollama_client import OllamaClient
    return OllamaClient()
