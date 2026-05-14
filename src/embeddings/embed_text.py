from __future__ import annotations

import os

from dotenv import load_dotenv
from openai import OpenAI

from classification.classify_slide import MissingOpenAIAPIKeyError


DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


def embed_text(text: str, model: str | None = None) -> list[float]:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise MissingOpenAIAPIKeyError(
            "OPENAI_API_KEY is missing. Add it to .env before generating embeddings."
        )

    embedding_model = model or os.getenv("OPENAI_EMBEDDING_MODEL") or DEFAULT_EMBEDDING_MODEL
    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(
        model=embedding_model,
        input=text,
    )
    return [float(value) for value in response.data[0].embedding]
