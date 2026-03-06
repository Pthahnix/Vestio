"""End-to-end pipeline: raw JSON → download → VLM → embed → LanceDB."""
from __future__ import annotations

import json
import uuid
from typing import Any

from processor.downloader import download_image
from processor.vlm import extract_attributes
from processor.embedder import FashionEmbedder
from store.db import VestioStore


def _raw_post_to_store_post(raw: dict) -> dict:
    """Convert collector RawPost format to store posts table format."""
    return {
        "id": raw["id"],
        "platform": raw["platform"],
        "source_url": raw["url"],
        "author_id": raw["authorId"],
        "author_name": raw.get("authorUsername") or raw.get("authorFullName") or "",
        "author_followers": 0,  # not available from collector
        "published_at": raw["publishedAt"],
        "caption": raw.get("caption", ""),
        "hashtags": raw.get("hashtags", []),
        "transcript": None,
        "likes": raw.get("likesCount", 0),
        "comments_count": raw.get("commentsCount", 0),
        "shares": 0,
        "media_type": raw.get("mediaType", "image"),
        "collected_at": raw.get("collectedAt", ""),
        "raw_metadata": json.dumps(raw.get("rawData", {})),
    }


def process_raw_posts(
    raw_json_path: str,
    db_path: str,
    vlm_model: str | None = None,
) -> dict[str, int]:
    """Process a JSON file of RawPosts into LanceDB.

    Returns stats dict with posts_processed, items_extracted, errors.
    """
    with open(raw_json_path) as f:
        raw_posts: list[dict] = json.load(f)

    store = VestioStore(db_path)
    embedder = FashionEmbedder()

    stats: dict[str, int] = {
        "posts_processed": 0,
        "items_extracted": 0,
        "errors": 0,
    }

    for raw_post in raw_posts:
        stats["posts_processed"] += 1

        # 1. Store post metadata
        store_post = _raw_post_to_store_post(raw_post)
        store.add_posts([store_post])

        # 2. Process each image
        image_urls = raw_post.get("imageUrls", [])
        for img_url in image_urls:
            image_bytes = download_image(img_url)
            if image_bytes is None:
                stats["errors"] += 1
                continue

            # 3. VLM attribute extraction
            try:
                clothing_items = extract_attributes(image_bytes, model=vlm_model)
            except Exception:
                stats["errors"] += 1
                continue

            # 4. Embed + store each detected item
            for item_attrs in clothing_items:
                try:
                    embedding = embedder.embed_image_bytes(image_bytes)
                    store_item = {
                        "id": str(uuid.uuid4()),
                        "post_id": raw_post["id"],
                        "image": image_bytes,
                        "image_embedding": embedding,
                        "category": item_attrs.get("category", ""),
                        "subtype": item_attrs.get("subtype", ""),
                        "colors": item_attrs.get("colors", []),
                        "pattern": item_attrs.get("pattern", ""),
                        "material": item_attrs.get("material", ""),
                        "style_tags": item_attrs.get("style_tags", []),
                        "brand": item_attrs.get("brand"),
                        "season": item_attrs.get("season"),
                        "occasion": item_attrs.get("occasion"),
                        "confidence": item_attrs.get("confidence", 0.0),
                        "bbox": item_attrs.get("bbox", []),
                    }
                    store.add_items([store_item])
                    stats["items_extracted"] += 1
                except Exception:
                    stats["errors"] += 1

    return stats
