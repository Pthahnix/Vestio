"""VLM-based clothing attribute extraction via OpenRouter."""
from __future__ import annotations

import base64
import json
import os
import re

from openai import OpenAI

from processor.prompts import FASHION_EXTRACTION_PROMPT


def _detect_media_type(image_bytes: bytes) -> str:
    """Detect image media type from magic bytes."""
    if image_bytes[:4] == b"\x89PNG":
        return "image/png"
    if image_bytes[:4] == b"RIFF" and len(image_bytes) > 11 and image_bytes[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def parse_vlm_response(raw_text: str) -> list[dict]:
    """Parse VLM response text into a list of clothing item dicts."""
    text = raw_text.strip()

    # Strip markdown code fences if present
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        # Some models wrap in {"items": [...]}
        if isinstance(parsed, dict) and "items" in parsed:
            return parsed["items"]
        return []
    except (json.JSONDecodeError, ValueError):
        return []


def extract_attributes(
    image_bytes: bytes,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
) -> list[dict]:
    """Extract clothing attributes from an image using VLM via OpenRouter.

    Args:
        image_bytes: Raw image bytes (JPEG/PNG/WebP).
        model: Model ID (default: env VLM_MODEL or google/gemini-2.5-flash).
        api_key: OpenRouter API key (default: env OPENROUTER_API_KEY).
        base_url: OpenRouter base URL (default: env OPENROUTER_BASE_URL).

    Returns:
        List of clothing item attribute dicts.
    """
    model = model or os.environ.get("VLM_MODEL", "google/gemini-2.5-flash")
    api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    base_url = base_url or os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

    client = OpenAI(api_key=api_key, base_url=base_url)

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    media_type = _detect_media_type(image_bytes)

    response = client.chat.completions.create(
        model=model,
        max_tokens=2048,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{b64}",
                    },
                },
                {
                    "type": "text",
                    "text": FASHION_EXTRACTION_PROMPT,
                },
            ],
        }],
    )

    return parse_vlm_response(response.choices[0].message.content or "")
