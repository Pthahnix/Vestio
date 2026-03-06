"""FashionCLIP embedding generator."""
from __future__ import annotations

import io

import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel

MODEL_ID = "patrickjohncyh/fashion-clip"
EMBEDDING_DIM = 512


class FashionEmbedder:
    """Generate 512-dim FashionCLIP embeddings for clothing images."""

    def __init__(self, model_id: str = MODEL_ID, device: str | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = CLIPModel.from_pretrained(model_id).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_id)
        self.model.eval()

    def embed_image(self, image: Image.Image) -> list[float]:
        """Embed a single PIL Image, returns normalized 512-dim vector."""
        inputs = self.processor(images=image, return_tensors="pt").to(self.device)
        with torch.no_grad():
            output = self.model.get_image_features(**inputs)
            # transformers 5.x returns BaseModelOutputWithPooling
            features = output.pooler_output if hasattr(output, "pooler_output") else output
            features = features / features.norm(dim=-1, keepdim=True)
        return features[0].cpu().tolist()

    def embed_images(self, images: list[Image.Image]) -> list[list[float]]:
        """Embed a batch of PIL Images."""
        inputs = self.processor(images=images, return_tensors="pt", padding=True).to(
            self.device
        )
        with torch.no_grad():
            output = self.model.get_image_features(**inputs)
            features = output.pooler_output if hasattr(output, "pooler_output") else output
            features = features / features.norm(dim=-1, keepdim=True)
        return features.cpu().tolist()

    def embed_image_bytes(self, image_bytes: bytes) -> list[float]:
        """Embed from raw image bytes (JPEG/PNG)."""
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        return self.embed_image(image)
