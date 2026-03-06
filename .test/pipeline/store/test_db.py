"""Component tests for LanceDB store schema and CRUD operations."""
import os
import tempfile
import numpy as np
import pytest

from store.schema import POSTS_SCHEMA, ITEMS_SCHEMA
from store.db import VestioStore


@pytest.fixture
def tmp_db_path():
    with tempfile.TemporaryDirectory() as d:
        yield os.path.join(d, "test.lance")


@pytest.fixture
def store(tmp_db_path):
    return VestioStore(tmp_db_path)


# --- Schema tests ---

class TestSchema:
    def test_posts_schema_has_required_fields(self):
        field_names = [f.name for f in POSTS_SCHEMA]
        for name in ["id", "platform", "source_url", "caption", "hashtags",
                      "likes", "comments_count", "media_type", "collected_at"]:
            assert name in field_names, f"Missing field: {name}"

    def test_items_schema_has_required_fields(self):
        field_names = [f.name for f in ITEMS_SCHEMA]
        for name in ["id", "post_id", "image", "image_embedding", "category",
                      "subtype", "colors", "pattern", "material", "style_tags",
                      "confidence", "bbox"]:
            assert name in field_names, f"Missing field: {name}"

    def test_items_embedding_is_512_dim(self):
        emb_field = ITEMS_SCHEMA.field("image_embedding")
        assert emb_field.type.list_size == 512


# --- Store CRUD tests ---

class TestVestioStoreInit:
    def test_creates_tables_on_init(self, store):
        names = store.table_names()
        assert "posts" in names
        assert "items" in names

    def test_idempotent_init(self, tmp_db_path):
        s1 = VestioStore(tmp_db_path)
        s2 = VestioStore(tmp_db_path)
        assert s2.table_names() == s1.table_names()


class TestPosts:
    def _make_post(self, post_id="post-001", caption="Test post #fashion"):
        return {
            "id": post_id,
            "platform": "instagram",
            "source_url": "https://instagram.com/p/ABC",
            "author_id": "user-1",
            "author_name": "tester",
            "author_followers": 1000,
            "published_at": "2026-03-01T10:00:00Z",
            "caption": caption,
            "hashtags": ["fashion"],
            "transcript": None,
            "likes": 50,
            "comments_count": 5,
            "shares": 0,
            "media_type": "image",
            "collected_at": "2026-03-06T12:00:00Z",
            "raw_metadata": "{}",
        }

    def test_insert_and_read_post(self, store):
        store.add_posts([self._make_post()])
        results = store.get_posts(where="id = 'post-001'")
        assert len(results) == 1
        assert results[0]["caption"] == "Test post #fashion"

    def test_insert_multiple_posts(self, store):
        posts = [self._make_post(f"post-{i:03d}", f"Caption {i}") for i in range(20)]
        store.add_posts(posts)
        results = store.get_posts(limit=50)
        assert len(results) == 20

    def test_filter_by_platform(self, store):
        store.add_posts([self._make_post()])
        results = store.get_posts(where="platform = 'instagram'")
        assert len(results) == 1
        results = store.get_posts(where="platform = 'tiktok'")
        assert len(results) == 0

    def test_unicode_caption(self, store):
        post = self._make_post("uni-001", "这件裙子太美了 🌸 #穿搭")
        store.add_posts([post])
        results = store.get_posts(where="id = 'uni-001'")
        assert "🌸" in results[0]["caption"]


class TestItems:
    def _make_item(self, item_id="item-001", category="top", embedding_val=0.1):
        vec = np.random.randn(512).astype(np.float32)
        vec = vec / np.linalg.norm(vec)
        return {
            "id": item_id,
            "post_id": "post-001",
            "image": b"\x89PNG fake image bytes",
            "image_embedding": vec.tolist(),
            "category": category,
            "subtype": "t-shirt",
            "colors": ["white"],
            "pattern": "solid",
            "material": "cotton",
            "style_tags": ["casual"],
            "brand": None,
            "season": "summer",
            "occasion": "everyday",
            "confidence": 0.95,
            "bbox": [0.1, 0.2, 0.5, 0.8],
        }

    def test_insert_and_search_items(self, store):
        item = self._make_item()
        store.add_items([item])
        results = store.search_items(item["image_embedding"], limit=1)
        assert len(results) == 1
        assert results[0]["id"] == "item-001"

    def test_search_returns_closest(self, store):
        items = [
            self._make_item("item-a", "top"),
            self._make_item("item-b", "bottom"),
        ]
        store.add_items(items)
        # Search with item-a's embedding should return item-a first
        results = store.search_items(items[0]["image_embedding"], limit=2)
        assert results[0]["id"] == "item-a"

    def test_search_with_category_filter(self, store):
        items = [
            self._make_item("item-top", "top"),
            self._make_item("item-shoe", "footwear"),
        ]
        store.add_items(items)
        results = store.search_items(
            items[0]["image_embedding"], limit=10, where="category = 'footwear'"
        )
        assert all(r["category"] == "footwear" for r in results)

    def test_bulk_insert_20_items(self, store):
        items = [self._make_item(f"item-{i:03d}", "top") for i in range(20)]
        store.add_items(items)
        results = store.search_items(items[0]["image_embedding"], limit=20)
        assert len(results) == 20

    def test_image_blob_metadata_on_search(self, store):
        """Blob-encoded image returns position/size metadata, not raw bytes."""
        item = self._make_item()
        item["image"] = b"\x89PNG test image data 1234567890"
        store.add_items([item])
        results = store.search_items(item["image_embedding"], limit=1)
        # LanceDB blob encoding returns metadata dict on search, not raw bytes
        blob_info = results[0]["image"]
        assert isinstance(blob_info, dict)
        assert "size" in blob_info
        assert blob_info["size"] == len(b"\x89PNG test image data 1234567890")
