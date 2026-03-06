"""E2E simulation test: full pipeline with 100 fake posts, realistic data."""
import random

import pytest
from unittest.mock import patch, MagicMock
from processor.pipeline import process_raw_posts
from store.db import VestioStore


class TestE2ESimulation:
    @patch("processor.pipeline.download_image")
    @patch("processor.pipeline.extract_attributes")
    @patch("processor.pipeline.FashionEmbedder")
    def test_100_posts_full_pipeline(
        self, MockEmbedder, mock_extract, mock_download,
        fake_posts_file_100, tmp_db_path,
        fake_jpeg_factory, fake_vlm_response_factory, normalized_embedding_factory,
    ):
        """Simulate processing 100 Instagram posts end-to-end.

        This test:
        - Generates 100 realistic fake posts (varied captions, hashtags, engagement)
        - Mocks image downloads with realistic JPEG data
        - Mocks VLM responses with varied item counts (0-5 items per image)
        - Mocks embeddings with random normalized vectors
        - Verifies all data is stored correctly in LanceDB
        - Verifies vector search returns relevant results
        - Verifies filtered search works
        """
        # Mock download returns realistic JPEG
        fake_jpeg = fake_jpeg_factory(640, 640)
        mock_download.return_value = fake_jpeg

        # Mock VLM returns varied realistic responses
        mock_extract.side_effect = lambda img_bytes, **kw: fake_vlm_response_factory()

        # Mock embedder returns random normalized vectors
        mock_instance = MagicMock()
        mock_instance.embed_image_bytes.side_effect = lambda b: normalized_embedding_factory()
        MockEmbedder.return_value = mock_instance

        # Run the pipeline
        stats = process_raw_posts(fake_posts_file_100, tmp_db_path)

        # Verify processing stats
        assert stats["posts_processed"] == 100
        assert stats["items_extracted"] > 0  # should have extracted many items
        print(f"\nSimulation stats: {stats}")
        print(f"  Average items per post: {stats['items_extracted'] / 100:.1f}")

        # Verify data is in LanceDB
        store = VestioStore(tmp_db_path)

        # All 100 posts should be stored
        posts = store.get_posts(limit=200)
        assert len(posts) == 100

        # Items should be searchable
        query_vec = normalized_embedding_factory()
        results = store.search_items(query_vec, limit=10)
        assert len(results) <= 10
        assert len(results) > 0

        # Category filter should work
        for category in ["top", "bottom", "dress", "outerwear", "footwear", "accessory"]:
            filtered = store.search_items(
                query_vec, limit=100, where=f"category = '{category}'"
            )
            assert all(r["category"] == category for r in filtered)

        # All items should have valid embeddings
        all_items = store.search_items(query_vec, limit=1000)
        for item in all_items:
            assert len(item["image_embedding"]) == 512
            # Verify embedding is normalized
            norm = sum(v * v for v in item["image_embedding"]) ** 0.5
            assert abs(norm - 1.0) < 0.05, f"Embedding not normalized: norm={norm}"

    @patch("processor.pipeline.download_image")
    @patch("processor.pipeline.extract_attributes")
    @patch("processor.pipeline.FashionEmbedder")
    def test_handles_mixed_failures_gracefully(
        self, MockEmbedder, mock_extract, mock_download,
        fake_posts_file_100, tmp_db_path,
        fake_jpeg_factory, fake_vlm_response_factory, normalized_embedding_factory,
    ):
        """Simulate realistic failure scenarios mixed in with successes."""
        call_count = {"n": 0}

        def flaky_download(url, **kw):
            call_count["n"] += 1
            # 20% of downloads fail
            if call_count["n"] % 5 == 0:
                return None
            return fake_jpeg_factory(640, 640)

        mock_download.side_effect = flaky_download

        def flaky_vlm(img_bytes, **kw):
            # 10% of VLM calls raise exceptions
            if random.random() < 0.1:
                raise Exception("VLM API timeout")
            return fake_vlm_response_factory()

        mock_extract.side_effect = flaky_vlm

        mock_instance = MagicMock()
        mock_instance.embed_image_bytes.side_effect = lambda b: normalized_embedding_factory()
        MockEmbedder.return_value = mock_instance

        stats = process_raw_posts(fake_posts_file_100, tmp_db_path)

        # All posts should be attempted
        assert stats["posts_processed"] == 100
        # Some items should succeed despite failures
        assert stats["items_extracted"] > 0
        # Some errors are expected
        assert stats["errors"] > 0
        print(f"\nFlaky simulation stats: {stats}")
