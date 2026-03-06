"""Component tests for VLM response parsing and attribute extraction."""
import json
import pytest
from unittest.mock import patch, MagicMock
from processor.vlm import extract_attributes, parse_vlm_response


class TestParseVlmResponse:
    def test_parses_valid_json_array(self):
        raw = json.dumps([{
            "category": "top",
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
        }])
        result = parse_vlm_response(raw)
        assert len(result) == 1
        assert result[0]["category"] == "top"
        assert result[0]["confidence"] == 0.95

    def test_handles_json_with_markdown_fences(self):
        raw = '```json\n[{"category": "bottom", "subtype": "jeans", "colors": ["blue"], "pattern": "solid", "material": "denim", "style_tags": ["casual"], "brand": null, "season": null, "occasion": null, "confidence": 0.9, "bbox": [0.1, 0.5, 0.5, 1.0]}]\n```'
        result = parse_vlm_response(raw)
        assert len(result) == 1
        assert result[0]["subtype"] == "jeans"

    def test_handles_wrapped_items_dict(self):
        """Some models return {"items": [...]} instead of bare array."""
        raw = json.dumps({"items": [
            {"category": "dress", "subtype": "maxi", "colors": ["red"],
             "pattern": "floral", "material": "cotton", "style_tags": ["bohemian"],
             "brand": None, "season": "summer", "occasion": "date",
             "confidence": 0.88, "bbox": [0.05, 0.1, 0.95, 0.95]}
        ]})
        result = parse_vlm_response(raw)
        assert len(result) == 1
        assert result[0]["category"] == "dress"

    def test_returns_empty_on_invalid_json(self):
        result = parse_vlm_response("I cannot analyze this image")
        assert result == []

    def test_returns_empty_on_empty_array(self):
        result = parse_vlm_response("[]")
        assert result == []

    def test_handles_multiple_items(self):
        items = [
            {"category": "top", "subtype": "blazer", "colors": ["navy"],
             "pattern": "solid", "material": "wool", "style_tags": ["formal"],
             "brand": "Zara", "season": "fall", "occasion": "work",
             "confidence": 0.91, "bbox": [0.1, 0.05, 0.9, 0.5]},
            {"category": "bottom", "subtype": "trousers", "colors": ["black"],
             "pattern": "solid", "material": "polyester", "style_tags": ["formal"],
             "brand": None, "season": None, "occasion": "work",
             "confidence": 0.87, "bbox": [0.1, 0.5, 0.9, 0.95]},
            {"category": "footwear", "subtype": "loafers", "colors": ["brown"],
             "pattern": "solid", "material": "leather", "style_tags": ["classic"],
             "brand": None, "season": None, "occasion": None,
             "confidence": 0.82, "bbox": [0.2, 0.85, 0.8, 1.0]},
        ]
        result = parse_vlm_response(json.dumps(items))
        assert len(result) == 3
        categories = [r["category"] for r in result]
        assert categories == ["top", "bottom", "footwear"]

    def test_handles_whitespace_and_newlines(self):
        raw = '\n\n  [{"category":"accessory","subtype":"watch","colors":["silver"],"pattern":"solid","material":"metal","style_tags":["classic"],"brand":"Rolex","season":null,"occasion":null,"confidence":0.75,"bbox":[0.3,0.4,0.4,0.5]}]  \n'
        result = parse_vlm_response(raw)
        assert len(result) == 1
        assert result[0]["brand"] == "Rolex"


class TestExtractAttributes:
    @patch("processor.vlm.OpenAI")
    def test_calls_openrouter_and_returns_items(self, MockOpenAI):
        """extract_attributes calls OpenRouter VLM API with base64 image."""
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = json.dumps([{
            "category": "dress",
            "subtype": "maxi dress",
            "colors": ["red", "white"],
            "pattern": "floral",
            "material": "cotton",
            "style_tags": ["bohemian"],
            "brand": None,
            "season": "summer",
            "occasion": "date",
            "confidence": 0.88,
            "bbox": [0.05, 0.1, 0.95, 0.95],
        }])
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        image_bytes = b"\x89PNG fake image data"
        result = extract_attributes(
            image_bytes,
            model="google/gemini-2.5-flash",
            api_key="test-key",
            base_url="https://openrouter.ai/api/v1",
        )

        assert len(result) == 1
        assert result[0]["category"] == "dress"
        assert result[0]["pattern"] == "floral"

        # Verify API was called correctly
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs["model"] == "google/gemini-2.5-flash"
        messages = call_args.kwargs["messages"]
        content = messages[0]["content"]
        assert any(c["type"] == "image_url" for c in content)
        assert any(c["type"] == "text" for c in content)

    @patch("processor.vlm.OpenAI")
    def test_handles_empty_response(self, MockOpenAI):
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = "[]"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        result = extract_attributes(b"\xff\xd8\xff\xe0 jpeg", api_key="k", base_url="u")
        assert result == []

    @patch("processor.vlm.OpenAI")
    def test_detects_png_media_type(self, MockOpenAI):
        mock_client = MagicMock()
        MockOpenAI.return_value = mock_client

        mock_choice = MagicMock()
        mock_choice.message.content = "[]"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        extract_attributes(b"\x89PNG\r\n\x1a\n rest of png", api_key="k", base_url="u")

        call_args = mock_client.chat.completions.create.call_args
        content = call_args.kwargs["messages"][0]["content"]
        image_part = [c for c in content if c["type"] == "image_url"][0]
        assert "data:image/png;base64," in image_part["image_url"]["url"]
