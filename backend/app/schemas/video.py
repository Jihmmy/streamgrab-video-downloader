"""
Schémas Pydantic pour les données vidéo.

Pourquoi Pydantic ?
- Validation automatique des données entrantes/sortantes
- Documentation API générée automatiquement (OpenAPI/Swagger)
- Typage strict : les erreurs sont détectées au plus tôt
- Sérialisation/désérialisation JSON natives
"""

from pydantic import BaseModel, Field
from typing import Optional


class VideoInfoRequest(BaseModel):
    """Requête pour analyser une vidéo à partir d'une URL."""
    url: str = Field(
        ...,
        description="URL de la vidéo à analyser (YouTube, Vimeo, Dailymotion, etc.)",
        json_schema_extra={"example": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    )


class FormatInfo(BaseModel):
    """Information sur un format disponible."""
    format_id: str = Field(..., description="Identifiant technique du format")
    ext: str = Field(..., description="Extension du fichier (mp4, webm, etc.)")
    quality: Optional[str] = Field(None, description="Label de qualité (1080p, 720p, etc.)")
    filesize: Optional[int] = Field(None, description="Taille estimée en octets")
    filesize_mb: Optional[float] = Field(None, description="Taille estimée en Mo")
    has_audio: bool = Field(True, description="Contient une piste audio")
    has_video: bool = Field(True, description="Contient une piste vidéo")
    is_mp4_compatible: bool = Field(False, description="Peut être converti en MP4")
    is_mp3_compatible: bool = Field(False, description="Peut être converti en MP3")


class VideoInfoResponse(BaseModel):
    """Réponse complète avec les métadonnées de la vidéo."""
    title: str = Field(..., description="Titre de la vidéo")
    duration: Optional[int] = Field(None, description="Durée en secondes")
    duration_formatted: Optional[str] = Field(None, description="Durée formatée (mm:ss)")
    thumbnail: Optional[str] = Field(None, description="URL de la miniature")
    webpage_url: str = Field(..., description="URL originale de la vidéo")
    uploader: Optional[str] = Field(None, description="Nom de l'auteur/chaine")
    upload_date: Optional[str] = Field(None, description="Date de publication (YYYYMMDD)")
    description: Optional[str] = Field(None, description="Description de la vidéo")
    formats: list[FormatInfo] = Field(default_factory=list, description="Formats disponibles")
    available_formats: list[str] = Field(
        default_factory=list,
        description="Formats de sortie disponibles (mp4, mp3)",
    )


class VideoDownloadRequest(BaseModel):
    """Requête pour télécharger une vidéo."""
    url: str = Field(
        ...,
        description="URL de la vidéo à télécharger",
        json_schema_extra={"example": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
    )
    format: str = Field(
        ...,
        description="Format de sortie souhaité (mp4 ou mp3)",
        pattern="^(mp4|mp3)$",
        json_schema_extra={"example": "mp4"},
    )


class ErrorResponse(BaseModel):
    """Réponse d'erreur standardisée."""
    error: str = Field(..., description="Message d'erreur")
    detail: Optional[str] = Field(None, description="Détail technique de l'erreur")


class DownloadStartResponse(BaseModel):
    """Réponse après le lancement d'un téléchargement asynchrone."""
    task_id: str = Field(..., description="Identifiant unique de la tâche de téléchargement")
    status: str = Field("pending", description="Statut initial de la tâche")


class DownloadProgressResponse(BaseModel):
    """Progression d'un téléchargement asynchrone."""
    task_id: str = Field(..., description="Identifiant unique de la tâche")
    url: str = Field(..., description="URL de la vidéo en cours de téléchargement")
    format: str = Field(..., description="Format de sortie demandé")
    status: str = Field(..., description="Statut actuel (pending/downloading/processing/completed/error)")
    progress: float = Field(0.0, description="Pourcentage d'avancement (0-100)")
    filename: Optional[str] = Field(None, description="Nom du fichier téléchargé (si terminé)")
    error: Optional[str] = Field(None, description="Message d'erreur (si échec)")
    speed: Optional[str] = Field(None, description="Vitesse de téléchargement affichable (ex: '2.5 MiB/s')")
    eta: Optional[int] = Field(None, description="Temps restant estimé en secondes")
