"""
Tests unitaires pour le service vidéo.

Teste la logique métier sans appeler l'API HTTP.
Utilise des URLs factices pour valider la validation et la gestion d'erreurs.
"""

import pytest
from app.services.video_service import _is_url_valid, _format_duration


class TestUrlValidation:
    """Tests de validation d'URL."""

    def test_valid_https_url(self):
        assert _is_url_valid("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_valid_http_url(self):
        assert _is_url_valid("http://example.com/video") is True

    def test_valid_url_with_params(self):
        assert _is_url_valid("https://youtu.be/dQw4w9WgXcQ?si=abc123") is True

    def test_valid_vimeo_url(self):
        assert _is_url_valid("https://vimeo.com/123456789") is True

    def test_invalid_empty_string(self):
        assert _is_url_valid("") is False

    def test_invalid_no_protocol(self):
        assert _is_url_valid("not-a-url") is False

    def test_invalid_ftp_url(self):
        assert _is_url_valid("ftp://files.com/video.mp4") is False

    def test_invalid_javascript(self):
        assert _is_url_valid("javascript:alert(1)") is False


class TestDurationFormatting:
    """Tests de formatage de la durée."""

    def test_none_duration(self):
        assert _format_duration(None) is None

    def test_zero_seconds(self):
        assert _format_duration(0) == "0:00"

    def test_short_video(self):
        assert _format_duration(30) == "0:30"

    def test_one_minute(self):
        assert _format_duration(60) == "1:00"

    def test_typical_song(self):
        assert _format_duration(245) == "4:05"

    def test_long_video(self):
        assert _format_duration(3661) == "1:01:01"

    def test_movie_length(self):
        assert _format_duration(7200) == "2:00:00"


class TestVideoInfoService:
    """Tests pour le service d'analyse vidéo."""

    def test_invalid_url_raises_error(self):
        """Une URL invalide doit lever une ValueError."""
        from app.services.video_service import get_video_info
        with pytest.raises(ValueError, match="L'URL fournie n'est pas valide"):
            get_video_info("not-a-url")

    def test_empty_url_raises_error(self):
        """Une URL vide doit lever une ValueError."""
        from app.services.video_service import get_video_info
        with pytest.raises(ValueError, match="L'URL fournie n'est pas valide"):
            get_video_info("")


class TestDownloadService:
    """Tests pour le service de téléchargement."""

    def test_invalid_format_raises_error(self):
        """Un format invalide doit lever une ValueError."""
        from app.services.video_service import download_video
        with pytest.raises(ValueError, match="Format non supporté"):
            download_video("https://example.com/video", "avi")

    def test_invalid_url_raises_error(self):
        """Une URL vide doit lever une ValueError."""
        from app.services.video_service import download_video
        with pytest.raises(ValueError, match="L'URL fournie n'est pas valide"):
            download_video("", "mp4")
