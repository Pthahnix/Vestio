"""Component tests for end-to-end pipeline runner."""
import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock
from processor.pipeline import process_raw_posts, _raw_post_to_store_post


@pytest.fixture
def raw_posts_file():
    """Create a temp file with raw Instagram posts."""
    posts = [
        {
            "id": "post-001",
            "platform": "instagram",
            "platformPostId": "ig-123",
            "url": "https://instagram.com/p/ABC",
            "caption": "Test outfit #fashion #ootd",
            "hashtags": ["fashion", "ootd"],
            "imageUrls": ["https://example.com/img1.jpg"],
            "authorId": "user-1",
            "authorUsername": "tester",
            "authorFullName": "Test User",
            "likesCount": 100,
            "commentsCount": 5,
            "publishedAt": "2026-03-01T10:00:00Z",
            "collectedAt": "2026-03-06T12:00:00Z",
            "mediaType": "image",
            "locationName": "Paris",
            "rawData": {},
        }
    ]
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(posts, f)
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def multi_posts_file():
    """Create a temp file with multiple posts, some with multiple images."""
    posts = [
        {
            "id": "post-001",
            "platform": "instagram",
            "platformPostId": "ig-1",
            "url": "https://instagram.com/p/A",
            "caption": "Look 1 #fashion",
            "hashtags": ["fashion"],
            "imageUrls": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
            "authorId": "user-1",
            "authorUsername": "alice",
            "authorFullName": "Alice",
            "likesCount": 200,
            "commentsCount": 10,
            "publishedAt": "2026-03-01T10:00:00Z",
            "collectedAt": "2026-03-06T12:00:00Z",
            "mediaType": "carousel",
            "locationName": None,
            "rawData": {},
        },
        {
            "id": "post-002",
            "platform": "instagram",
            "platformPostId": "ig-2",
            "url": "https://instagram.com/p/B",
            "caption": "Look 2",
            "hashtags": [],
            "imageUrls": ["https://example.com/img3.jpg"],
            "authorId": "user-2",
            "authorUsername": "bob",
            "authorFullName": "Bob",
            "likesCount": 50,
            "commentsCount": 2,
            "publishedAt": "2026-03-02T10:00:00Z",
            "collectedAt": "2026-03-06T12:00:00Z",
            "mediaType": "image",
            "locationName": "Tokyo",
            "rawData": {},
        },
    ]
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(posts, f)
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def tmp_db_path():
    with tempfile.TemporaryDirectory() as d:
        yield os.path.join(d, "test.lance")


class TestRawPostConversion:
    def test_converts_collector_format_to_store_format(self):
        raw = {
            "id": "post-001",
            "platform": "instagram",
            "url": "https://instagram.com/p/ABC",
            "authorId": "user-1",
            "authorUsername": "tester",
            "authorFullName": "Test User",
            "publishedAt": "2026-03-01T10:00:00Z",
            "caption": "Hello #fashion",
            "hashtags": ["fashion"],
            "likesCount": 100,
            "commentsCount": 5,
            "collectedAt": "2026-03-06T12:00:00Z",
            "mediaType": "image",
            "rawData": {"extra": "data"},
        }
        result = _raw_post_to_store_post(raw)
        assert result["id"] == "post-001"
        assert result["platform"] == "instagram"
        assert result["source_url"] == "https://instagram.com/p/ABC"
        assert result["author_id"] == "user-1"
        assert result["author_name"] == "tester"
        assert result["caption"] == "Hello #fashion"
        assert result["hashtags"] == ["fashion"]
        assert result["likes"] == 100
        assert result["media_type"] == "image"
        assert result["raw_metadata"] == '{"extra": "data"}'

    def test_falls_back_to_full_name(self):
        raw = {
            "id": "p1", "platform": "instagram", "url": "u",
            "authorId": "a1", "authorUsername": None,
            "authorFullName": "Full Name",
            "publishedAt": "t", "collectedAt": "t",
            "rawData": {},
        }
        result = _raw_post_to_store_post(raw)
        assert result["author_name"] == "Full Name"

    def test_handles_missing_optional_fields(self):
        raw = {
            "id": "p1", "platform": "instagram", "url": "u",
            "authorId": "a1", "publishedAt": "t", "collectedAt": "t",
            "rawData": {},
        }
        result = _raw_post_to_store_post(raw)
        assert result["caption"] == ""
        assert result["hashtags"] == []
        assert result["likes"] == 0
        assert result["media_type"] == "image"


class TestProcessRawPosts:
    @patch("processor.pipeline.download_image")
    @patch("processor.pipeline.extract_attributes")
    @patch("processor.pipeline.FashionEmbedder")
    def test_end_to_end(
        self, MockEmbedder, mock_extract, mock_download,
        raw_posts_file, tmp_db_path
    ):
        # Mock download
        mock_download.return_value = b"\x89PNG fake image"

        # Mock VLM extraction
        mock_extract.return_value = [{
            "category": "top",
            "subtype": "t-shirt",
            "colors": ["white"],
            "pattern": "solid",
            "material": "cotton",
            "style_tags": ["casual"],
            "brand": None,
            "season": "summer",
            "occasion": "everyday",
            "confidence": 0.9,
            "bbox": [0.1, 0.2, 0.5, 0.8],
        }]

        # Mock embedder
        mock_embedder_instance = MagicMock()
        mock_embedder_instance.embed_image_bytes.return_value = [0.1] * 512
        MockEmbedder.return_value = mock_embedder_instance

        stats = process_raw_posts(raw_posts_file, tmp_db_path)

        assert stats["posts_processed"] == 1
        assert stats["items_extracted"] == 1
        assert stats["errors"] == 0

        # Verify data is in LanceDB
        from store.db import VestioStore
        store = VestioStore(tmp_db_path)
        posts = store.get_posts()
        assert len(posts) == 1

        items = store.search_items([0.1] * 512, limit=10)
        assert len(items) == 1
        assert items[0]["category"] == "top"

    @patch("processor.pipeline.download_image")
    @patch("processor.pipeline.extract_attributes")
    @patch("processor.pipeline.FashionEmbedder")
    def test_handles_download_failure(
        self, MockEmbedder, mock_extract, mock_download,
        raw_posts_file, tmp_db_path
    ):
        mock_download.return_value = None  # download fails

        mock_embedder_instance = MagicMock()
        MockEmbedder.return_value = mock_embedder_instance

        stats = process_raw_posts(raw_posts_file, tmp_db_path)

        assert stats["posts_processed"] == 1
        assert stats["items_extracted"] == 0
        # VLM should not be called if download failed
        mock_extract.assert_not_called()

    @patch("processor.pipeline.download_image")
    @patch("processor.pipeline.extract_attributes")
    @patch("processor.pipeline.FashionEmbedder")
    def test_handles_vlm_exception(
        self, MockEmbedder, mock_extract, mock_download,
        raw_posts_file, tmp_db_path
    ):
        """VLM errors are counted but don't crash the pipeline."""
        mock_download.return_value = b"\x89PNG image"
        mock_extract.side_effect = Exception("VLM API timeout")

        mock_embedder_instance = MagicMock()
        MockEmbedder.return_value = mock_embedder_instance

        stats = process_raw_posts(raw_posts_file, tmp_db_path)

        assert stats["posts_processed"] == 1
        assert stats["items_extracted"] == 0
        assert stats["errors"] == 1

    @patch("processor.pipeline.download_image")
    @patch("processor.pipeline.extract_attributes")
    @patch("processor.pipeline.FashionEmbedder")
    def test_multiple_posts_multiple_images(
        self, MockEmbedder, mock_extract, mock_download,
        multi_posts_file, tmp_db_path
    ):
        """Processes multiple posts with multiple images each."""
        mock_download.return_value = b"\xff\xd8 jpeg"

        mock_extract.return_value = [{
            "category": "top", "subtype": "blouse",
            "colors": ["pink"], "pattern": "solid",
            "material": "silk", "style_tags": ["romantic"],
            "brand": None, "season": None, "occasion": None,
            "confidence": 0.85, "bbox": [0.1, 0.1, 0.9, 0.9],
        }]

        mock_embedder_instance = MagicMock()
        mock_embedder_instance.embed_image_bytes.return_value = [0.05] * 512
        MockEmbedder.return_value = mock_embedder_instance

        stats = process_raw_posts(multi_posts_file, tmp_db_path)

        # 2 posts, first has 2 images, second has 1 image = 3 items
        assert stats["posts_processed"] == 2
        assert stats["items_extracted"] == 3
        assert stats["errors"] == 0

    @patch("processor.pipeline.download_image")
    @patch("processor.pipeline.extract_attributes")
    @patch("processor.pipeline.FashionEmbedder")
    def test_vlm_returns_empty_list(
        self, MockEmbedder, mock_extract, mock_download,
        raw_posts_file, tmp_db_path
    ):
        """VLM finding no clothing items results in 0 items extracted."""
        mock_download.return_value = b"\x89PNG image"
        mock_extract.return_value = []  # no clothing detected

        mock_embedder_instance = MagicMock()
        MockEmbedder.return_value = mock_embedder_instance

        stats = process_raw_posts(raw_posts_file, tmp_db_path)

        assert stats["posts_processed"] == 1
        assert stats["items_extracted"] == 0
        assert stats["errors"] == 0
