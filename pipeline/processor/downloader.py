"""Download images from URLs."""
from __future__ import annotations

import requests


def download_image(url: str, timeout: int = 30) -> bytes | None:
    """Download image bytes from a URL. Returns None on failure."""
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None


def download_images(urls: list[str], timeout: int = 30) -> list[bytes]:
    """Download multiple images, skipping failures."""
    results = []
    for url in urls:
        data = download_image(url, timeout)
        if data is not None:
            results.append(data)
    return results
