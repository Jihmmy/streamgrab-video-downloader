"""
Tests d'intégration pour l'API REST.

Teste les endpoints HTTP en utilisant le TestClient FastAPI.
Permet de valider que les routes répondent correctement sans
avoir à lancer un vrai serveur.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Tests pour le endpoint /api/v1/health."""

    def test_health_check(self):
        """Le healthcheck doit retourner 200 avec un status healthy."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "StreamGrab API"
        assert data["version"] == "1.0.0"


class TestRootEndpoint:
    """Tests pour le endpoint racine."""

    def test_root_returns_info(self):
        """La racine doit retourner les infos de l'API."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "documentation" in data
        assert data["documentation"] == "/docs"
        assert "version" in data


class TestVideoInfoEndpoint:
    """Tests pour POST /api/v1/video/info."""

    def test_invalid_url_returns_400(self):
        """URL invalide → 400 Bad Request."""
        response = client.post("/api/v1/video/info", json={"url": "not-a-url"})
        assert response.status_code == 400

    def test_empty_url_returns_400(self):
        """URL vide → 400 car notre validation métier la détecte avant Pydantic."""
        response = client.post("/api/v1/video/info", json={"url": ""})
        assert response.status_code == 400

    def test_missing_url_returns_422(self):
        """Pas d'URL → 422 car le champ est requis."""
        response = client.post("/api/v1/video/info", json={})
        assert response.status_code == 422

    def test_valid_request_structure(self):
        """Test que la structure de requête est bien acceptée."""
        response = client.post(
            "/api/v1/video/info",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )
        # Soit 200 (succès si connexion dispo), soit 400 (timeout/erreur réseau)
        # On vérifie juste que c'est pas une erreur 500
        assert response.status_code in (200, 400, 422)


class TestVideoDownloadEndpoint:
    """Tests pour POST /api/v1/video/download."""

    def test_missing_fields_returns_422(self):
        """Champs manquants → 422."""
        response = client.post("/api/v1/video/download", json={})
        assert response.status_code == 422

    def test_invalid_format_returns_400(self):
        """Format invalide → 400 (si l'URL est valide) ou 422 (si validation)."""
        response = client.post(
            "/api/v1/video/download",
            json={"url": "not-a-url", "format": "avi"}
        )
        assert response.status_code in (400, 422)

    def test_valid_format_structure(self):
        """Test que la structure requête/réponse est valide."""
        response = client.post(
            "/api/v1/video/download",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "format": "mp4"}
        )
        # Si le format est valide mais l'URL non accessible → 400
        # Si le format est invalide → 422
        assert response.status_code in (400, 422)