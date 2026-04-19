from __future__ import annotations

from importlib import import_module


def _async_openai_class():
    return import_module("openai").AsyncOpenAI


class LocalLLMClient:
    def __init__(self, base_url: str, api_key: str, model: str, temperature: float = 0.2) -> None:
        self._client = _async_openai_class()(base_url=base_url, api_key=api_key)
        self._model = model
        self._temperature = temperature

    async def generate_json(self, system_prompt: str, user_prompt: str, max_tokens: int = 512) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self._temperature,
            max_tokens=max_tokens,
            extra_body={
                "top_k": 20,
                "chat_template_kwargs": {"enable_thinking": False},
            },
        )
        return response.choices[0].message.content or ""


class LocalEmbeddingClient:
    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self._client = _async_openai_class()(base_url=base_url, api_key=api_key)
        self._model = model

    async def create_embedding(self, text: str) -> list[float]:
        response = await self._client.embeddings.create(
            input=[text],
            model=self._model,
        )
        return list(response.data[0].embedding)
