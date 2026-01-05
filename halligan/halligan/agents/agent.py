import base64
import io
from abc import ABC, abstractmethod
from typing import Any, Optional, TypeAlias

import openai
from PIL import Image

from halligan.utils.logger import Trace

Metadata: TypeAlias = dict[str, Any]


class Agent(ABC):
    @abstractmethod
    def __call__(
        self, prompt: str, images: Optional[list[Image.Image]] = None, image_captions: Optional[list[str]] = None
    ) -> tuple[str, Metadata]:
        pass

    @abstractmethod
    def reset(self) -> None:
        pass


class GPTAgent(Agent):
    def __init__(
        self,
        api_key: str | None,
        model: str = "gpt-4o-2024-11-20",
        *,
        timeout: int = 30,
    ) -> None:
        if not api_key or not isinstance(api_key, str):
            raise ValueError("Missing OPENAI_API_KEY (provide a non-empty string)")
        self.model = model
        self.client = openai.OpenAI(api_key=api_key, timeout=timeout)
        self.history: list[dict[str, Any]] = []

    def reset(self) -> None:
        self.history = []

    @Trace.agent()
    def __call__(
        self,
        prompt: str,
        images: Optional[list[Image.Image]] = None,
        image_captions: Optional[list[str]] = None,
    ) -> tuple[str, Metadata]:
        user_prompt = [{"type": "text", "text": prompt}]

        images = images or []
        if image_captions is None or len(image_captions) != len(images):
            image_captions = [f"Image {i}" for i in range(len(images))]

        for image, image_caption in zip(images, image_captions):
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG")
            image_b64 = base64.b64encode(buffer.getvalue()).decode("ascii")
            user_prompt.append({"type": "text", "text": image_caption})
            user_prompt.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}})

        self.history.append({"role": "user", "content": user_prompt})

        response = self.client.chat.completions.create(
            model=self.model, messages=self.history, max_tokens=1024, temperature=0, top_p=1
        )

        content = response.choices[0].message.content
        metadata = {
            "fingerprint": response.system_fingerprint,
            "total_tokens": response.usage.total_tokens,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
        }

        self.history.append({"role": "assistant", "content": content})

        return content, metadata
