"""Shared fixtures and realistic fake data generators for all pipeline tests."""
import io
import json
import os
import random
import string
import tempfile
import uuid

import numpy as np
import pytest
from PIL import Image


# --- Fake Data Constants ---

SAMPLE_CAPTIONS = [
    "Love this outfit! Perfect for a casual day out \U0001f338 #ootd #fashion #streetstyle",
    "New blazer from @zara paired with vintage denim \U0001f499 #workstyle #minimalist",
    "Summer vibes \u2600\ufe0f This dress is everything! #summerfashion #floral #beachready",
    "Keeping it simple today. Black on black never fails. #allblack #minimal #chic",
    "Thrifted this amazing leather jacket! \U0001f5a4 #thriftfind #vintage #sustainable",
    "Date night look \U0001f339 #datenight #elegant #littleblackdress",
    "Gym fit check \U0001f4aa #activewear #sporty #nike #fitcheck",
    "Layering season is here! Coat + scarf + boots = \u2764\ufe0f #fallfashion #layers",
    "\u8fd9\u4ef6\u8fde\u8863\u88d9\u592a\u7f8e\u4e86\uff01\u5468\u672b\u7a7f\u51fa\u53bb\u901b\u8857 #\u7a7f\u642d #\u65f6\u5c1a #\u65e5\u5e38",
    "Office look today: oversized blazer + wide-leg pants \U0001f454 #corporatestyle #9to5",
]

SAMPLE_HASHTAGS_POOL = [
    "ootd", "fashion", "streetstyle", "minimalist", "casual", "formal",
    "vintage", "sustainable", "thrift", "luxury", "sneakers", "denim",
    "floral", "summer", "winter", "spring", "fall", "workwear", "datenight",
    "activewear", "bohemian", "preppy", "grunge", "cottagecore", "darkacademia",
]

SAMPLE_VLM_ITEMS = [
    {"category": "top", "subtype": "t-shirt", "colors": ["white"], "pattern": "solid", "material": "cotton", "style_tags": ["casual"], "brand": None, "season": "summer", "occasion": "everyday", "confidence": 0.93},
    {"category": "top", "subtype": "blazer", "colors": ["navy"], "pattern": "solid", "material": "wool", "style_tags": ["formal", "minimalist"], "brand": "Zara", "season": "fall", "occasion": "work", "confidence": 0.91},
    {"category": "bottom", "subtype": "jeans", "colors": ["blue"], "pattern": "solid", "material": "denim", "style_tags": ["casual"], "brand": "Levi's", "season": None, "occasion": "everyday", "confidence": 0.88},
    {"category": "dress", "subtype": "maxi dress", "colors": ["red", "white"], "pattern": "floral", "material": "cotton", "style_tags": ["bohemian"], "brand": None, "season": "summer", "occasion": "date", "confidence": 0.85},
    {"category": "outerwear", "subtype": "leather jacket", "colors": ["black"], "pattern": "solid", "material": "leather", "style_tags": ["streetwear", "punk"], "brand": None, "season": "fall", "occasion": "everyday", "confidence": 0.90},
    {"category": "footwear", "subtype": "sneakers", "colors": ["white"], "pattern": "solid", "material": "leather", "style_tags": ["casual", "sporty"], "brand": "Nike", "season": None, "occasion": "everyday", "confidence": 0.95},
    {"category": "accessory", "subtype": "handbag", "colors": ["brown"], "pattern": "solid", "material": "leather", "style_tags": ["classic"], "brand": "Coach", "season": None, "occasion": None, "confidence": 0.82},
    {"category": "bottom", "subtype": "wide-leg pants", "colors": ["black"], "pattern": "solid", "material": "polyester", "style_tags": ["formal", "minimalist"], "brand": None, "season": None, "occasion": "work", "confidence": 0.87},
]


# --- Fake Data Generator Functions ---

def make_fake_jpeg(width: int = 640, height: int = 640) -> bytes:
    """Generate a realistic-sized fake JPEG image."""
    arr = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def make_fake_post(index: int) -> dict:
    """Generate a single realistic fake Instagram RawPost."""
    num_hashtags = random.randint(3, 15)
    hashtags = random.sample(SAMPLE_HASHTAGS_POOL, min(num_hashtags, len(SAMPLE_HASHTAGS_POOL)))
    caption = random.choice(SAMPLE_CAPTIONS)
    likes = int(random.paretovariate(1.5) * 50)
    comments = int(random.paretovariate(2.0) * 5)
    num_images = random.choices([1, 2, 3, 5, 10], weights=[50, 20, 15, 10, 5])[0]
    media_type = "carousel" if num_images > 1 else "image"

    return {
        "id": str(uuid.uuid4()),
        "platform": "instagram",
        "platformPostId": f"ig-{index}-{''.join(random.choices(string.ascii_lowercase, k=8))}",
        "url": f"https://www.instagram.com/p/{''.join(random.choices(string.ascii_uppercase + string.digits, k=11))}/",
        "caption": caption,
        "hashtags": hashtags,
        "imageUrls": [f"https://fake-cdn.example.com/img-{index}-{j}.jpg" for j in range(num_images)],
        "authorId": f"user-{random.randint(1000, 9999)}",
        "authorUsername": f"fashion_user_{index}",
        "authorFullName": f"Fashion User {index}",
        "likesCount": likes,
        "commentsCount": comments,
        "publishedAt": f"2026-{random.randint(1,3):02d}-{random.randint(1,28):02d}T{random.randint(0,23):02d}:{random.randint(0,59):02d}:00Z",
        "collectedAt": "2026-03-06T12:00:00Z",
        "mediaType": media_type,
        "locationName": random.choice(["Paris", "Tokyo", "New York", "London", "Milan", None, None]),
        "rawData": {},
    }


def make_fake_vlm_response(num_items: int | None = None) -> list[dict]:
    """Generate a realistic VLM response with random clothing items."""
    if num_items is None:
        num_items = random.choices([0, 1, 2, 3, 5], weights=[5, 30, 40, 20, 5])[0]
    if num_items == 0:
        return []
    items = random.sample(SAMPLE_VLM_ITEMS, min(num_items, len(SAMPLE_VLM_ITEMS)))
    result = []
    for i, item in enumerate(items):
        it = dict(item)
        y_start = i / max(num_items, 1)
        it["bbox"] = [0.1, round(y_start, 2), 0.9, round(min(y_start + 0.4, 1.0), 2)]
        result.append(it)
    return result


def make_normalized_embedding(dim: int = 512) -> list[float]:
    """Generate a random normalized embedding vector."""
    vec = np.random.randn(dim).astype(np.float32)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


# --- Pytest Fixtures ---

@pytest.fixture
def fake_posts_100():
    """Generate 100 fake Instagram posts."""
    return [make_fake_post(i) for i in range(100)]


@pytest.fixture
def fake_posts_file_100(fake_posts_100):
    """Write 100 fake posts to a temp JSON file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(fake_posts_100, f)
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def tmp_db_path():
    with tempfile.TemporaryDirectory() as d:
        yield os.path.join(d, "test.lance")


# Expose generator functions as fixtures for tests that need them
@pytest.fixture
def fake_jpeg_factory():
    """Returns the make_fake_jpeg function."""
    return make_fake_jpeg


@pytest.fixture
def fake_vlm_response_factory():
    """Returns the make_fake_vlm_response function."""
    return make_fake_vlm_response


@pytest.fixture
def normalized_embedding_factory():
    """Returns the make_normalized_embedding function."""
    return make_normalized_embedding
