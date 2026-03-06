"""Component tests for image downloader utility."""
import pytest
from unittest.mock import patch, MagicMock
from processor.downloader import download_image, download_images


class TestDownloadImage:
    @patch("processor.downloader.requests.get")
    def test_downloads_image_bytes(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"\x89PNG fake image"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = download_image("https://example.com/img.jpg")
        assert result == b"\x89PNG fake image"
        mock_get.assert_called_once()

    @patch("processor.downloader.requests.get")
    def test_returns_none_on_failure(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        result = download_image("https://bad-url.com/img.jpg")
        assert result is None

    @patch("processor.downloader.requests.get")
    def test_passes_timeout(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.content = b"data"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        download_image("https://example.com/img.jpg", timeout=10)
        mock_get.assert_called_once_with("https://example.com/img.jpg", timeout=10)

    @patch("processor.downloader.requests.get")
    def test_returns_none_on_http_error(self, mock_get):
        """HTTP errors (4xx, 5xx) should return None."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_resp

        result = download_image("https://example.com/missing.jpg")
        assert result is None


class TestDownloadImages:
    @patch("processor.downloader.requests.get")
    def test_downloads_multiple(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"image_data"
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        urls = ["https://a.com/1.jpg", "https://a.com/2.jpg"]
        results = download_images(urls)
        assert len(results) == 2
        assert all(r == b"image_data" for r in results)

    @patch("processor.downloader.requests.get")
    def test_skips_failures(self, mock_get):
        """Failures in batch are skipped, not raised."""
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("fail")
            resp = MagicMock()
            resp.content = b"ok"
            resp.raise_for_status = MagicMock()
            return resp

        mock_get.side_effect = side_effect

        urls = ["https://a.com/1.jpg", "https://a.com/2.jpg", "https://a.com/3.jpg"]
        results = download_images(urls)
        assert len(results) == 2

    @patch("processor.downloader.requests.get")
    def test_empty_list(self, mock_get):
        results = download_images([])
        assert results == []
        mock_get.assert_not_called()
