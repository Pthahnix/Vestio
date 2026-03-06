"""Component tests for FashionCLIP embedder."""
import io
import pytest
import numpy as np
from PIL import Image
from processor.embedder import FashionEmbedder, EMBEDDING_DIM


@pytest.fixture(scope="module")
def embedder():
    """Load model once for all tests in this module."""
    return FashionEmbedder()


@pytest.fixture
def dummy_image():
    """Create a simple 224x224 test image."""
    return Image.fromarray(
        np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
    )


class TestFashionEmbedder:
    def test_embedding_dim_constant(self):
        assert EMBEDDING_DIM == 512

    def test_embed_single_image(self, embedder, dummy_image):
        """Embedding a single image returns a 512-dim vector."""
        vec = embedder.embed_image(dummy_image)
        assert isinstance(vec, list)
        assert len(vec) == 512
        assert all(isinstance(v, float) for v in vec)

    def test_embed_batch(self, embedder, dummy_image):
        """Embedding a batch returns one vector per image."""
        images = [dummy_image, dummy_image, dummy_image]
        vecs = embedder.embed_images(images)
        assert len(vecs) == 3
        assert all(len(v) == 512 for v in vecs)

    def test_embed_from_bytes(self, embedder):
        """Can embed from raw image bytes."""
        img = Image.fromarray(
            np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        )
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        vec = embedder.embed_image_bytes(buf.getvalue())
        assert len(vec) == 512

    def test_embeddings_are_normalized(self, embedder, dummy_image):
        """Embeddings should be L2-normalized (unit vectors)."""
        vec = embedder.embed_image(dummy_image)
        norm = sum(v * v for v in vec) ** 0.5
        assert abs(norm - 1.0) < 0.01

    def test_different_images_produce_different_embeddings(self, embedder):
        """Two visually different images should produce different embeddings."""
        red_img = Image.fromarray(
            np.full((224, 224, 3), [200, 50, 50], dtype=np.uint8)
        )
        blue_img = Image.fromarray(
            np.full((224, 224, 3), [50, 50, 200], dtype=np.uint8)
        )
        v_red = embedder.embed_image(red_img)
        v_blue = embedder.embed_image(blue_img)

        # Should not be identical
        assert v_red != v_blue

        # Cosine similarity should be < 1.0
        sim = sum(a * b for a, b in zip(v_red, v_blue))
        assert sim < 0.99

    def test_similar_images_closer_than_different(self, embedder):
        """Two similar images should have higher cosine similarity."""
        red1 = Image.fromarray(np.full((224, 224, 3), [200, 50, 50], dtype=np.uint8))
        red2 = Image.fromarray(np.full((224, 224, 3), [190, 40, 60], dtype=np.uint8))
        blue = Image.fromarray(np.full((224, 224, 3), [50, 50, 200], dtype=np.uint8))

        v1 = embedder.embed_image(red1)
        v2 = embedder.embed_image(red2)
        v3 = embedder.embed_image(blue)

        sim_reds = sum(a * b for a, b in zip(v1, v2))
        sim_red_blue = sum(a * b for a, b in zip(v1, v3))
        assert sim_reds > sim_red_blue

    def test_embed_realistic_sized_image(self, embedder):
        """Can handle Instagram-sized images (1080x1350)."""
        img = Image.fromarray(
            np.random.randint(0, 255, (1350, 1080, 3), dtype=np.uint8)
        )
        vec = embedder.embed_image(img)
        assert len(vec) == 512
