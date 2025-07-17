import io
import base64
from abc import ABC, abstractmethod
from typing import Optional, TypeAlias, Any

import openai
from PIL import Image

from halligan.utils.logger import Trace


Metadata: TypeAlias = dict[str, Any]


class Agent(ABC):
    @abstractmethod
    def __call__(
        self, 
        prompt: str, images: Optional[list[Image.Image]] = None, 
        image_captions: Optional[list[str]] = None
    ) -> tuple[str, str]:
        pass

    @abstractmethod
    def reset(self):
        pass


class GPTAgent(Agent):
    def __init__(self, api_key: str, model: str = "gpt-4o-2024-11-20") -> None:
        self.model = model
        self.client = openai.OpenAI(api_key=api_key, timeout=30)
        self.history = []

    def reset(self):
        self.history = []
 
    @Trace.agent()
    def __call__(
        self, 
        prompt: str, 
        images: Optional[list[Image.Image]] = [],
        image_captions: Optional[list[str]] = []
    ) -> tuple[str, Metadata]:
        user_prompt = [{"type": "text", "text": prompt}]
        
        for image, image_caption in zip(images, image_captions):
            bytes = io.BytesIO()
            image.save(bytes, format="JPEG")
            image_b64 = base64.b64encode(bytes.getvalue()).decode('ascii')
            user_prompt.append({
                "type": "text",
                "text": image_caption
            })
            user_prompt.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
            })

        self.history.append({"role": "user", "content": user_prompt})

        print("history:", len(self.history))

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            max_tokens=1024,
            temperature=0,
            top_p=1
        )

        content = response.choices[0].message.content
        metadata = {
            "fingerprint": response.system_fingerprint,
            "total_tokens": response.usage.total_tokens,
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens
        }

        self.history.append({"role": "assistant", "content": content})
        
        return content, metadata