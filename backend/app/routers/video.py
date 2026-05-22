"""
Routes API pour l'analyse et le téléchargement de vidéos.

Pourquoi un router séparé ?
- Organise les endpoints par domaine fonctionnel
- Facilite l'évolution (ajout de nouvelles routes sans tout casser)
- Permet de monter le router dans main.py avec un préfixe commun
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse

from app.schemas.video import (
    VideoInfoRequest,
    VideoInfoResponse,
    VideoDownloadRequest,
    DownloadStartResponse,
    DownloadProgressResponse,
    ErrorResponse,
)
from app.services.video_service import get_video_info, download_video, cleanup_downloads
from app.services.download_manager import (
    start_download as start_async_download,
    get_progress,
    get_task_file_path,
    DownloadStatus,
)
from app.config import DOWNLOAD_DIR

logger = logging.getLogger(__name__)

# Création du router avec préfixe /api/v1
router = APIRouter(prefix="/api/v1", tags=["video"])


@router.post(
    "/video/info",
    response_model=VideoInfoResponse,
    responses={
        400: {"model": ErrorResponse, "description": "URL invalide"},
        422: {"model": ErrorResponse, "description": "Format de requête invalide"},
        500: {"model": ErrorResponse, "description": "Erreur serveur"},
    },
    summary="Analyser une vidéo",
    description=(
        "Analyse une vidéo à partir de son URL et retourne "
        "toutes ses métadonnées (titre, durée, miniature, formats disponibles)."
    ),
)
async def video_info(request: VideoInfoRequest):
    """
    Endpoint POST /api/v1/video/info

    Reçoit une URL vidéo et retourne les informations complètes :
    - Titre, durée, miniature
    - Auteur, date de publication
    - Liste des formats disponibles avec leurs caractéristiques
    - Formats de sortie disponibles (mp4, mp3)
    """
    try:
        result = get_video_info(request.url)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": str(e)},
        )
    except Exception as e:
        logger.exception("Erreur inattendue dans video_info")
        raise HTTPException(
            status_code=500,
            detail={"error": "Une erreur interne est survenue", "detail": str(e)},
        )


@router.post(
    "/video/download",
    responses={
        400: {"model": ErrorResponse, "description": "Requête invalide"},
        500: {"model": ErrorResponse, "description": "Erreur serveur"},
    },
    summary="Télécharger une vidéo",
    description=(
        "Télécharge une vidéo et la retourne dans le format demandé "
        "(MP4 pour la vidéo, MP3 pour l'audio uniquement)."
    ),
)
async def video_download(request: VideoDownloadRequest):
    """
    Endpoint POST /api/v1/video/download

    Télécharge une vidéo et retourne le fichier directement :
    - format="mp4" → fichier vidéo MP4
    - format="mp3" → fichier audio MP3
    """
    try:
        filepath = download_video(request.url, request.format)

        # Déterminer le media type pour la réponse
        media_type = (
            "audio/mpeg" if request.format == "mp3" else "video/mp4"
        )

        # Nettoyer les anciens fichiers
        cleanup_downloads(max_age_hours=1)

        return FileResponse(
            path=filepath,
            media_type=media_type,
            filename=filepath.name,
            headers={
                "Content-Disposition": f'attachment; filename="{filepath.name}"',
            },
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": str(e)},
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail={"error": "Fichier introuvable après téléchargement", "detail": str(e)},
        )
    except Exception as e:
        logger.exception("Erreur inattendue dans video_download")
        raise HTTPException(
            status_code=500,
            detail={"error": "Une erreur interne est survenue", "detail": str(e)},
        )


@router.get(
    "/video/info",
    response_model=VideoInfoResponse,
    responses={
        400: {"model": ErrorResponse, "description": "URL invalide ou manquante"},
        500: {"model": ErrorResponse, "description": "Erreur serveur"},
    },
    summary="Analyser une vidéo (GET)",
    description=(
        "Version GET de l'analyse vidéo. "
        "Utilisez le paramètre ?url= pour passer l'URL."
    ),
)
async def video_info_get(url: str = Query(..., description="URL de la vidéo à analyser")):
    """
    Endpoint GET /api/v1/video/info?url=...

    Alternative plus simple pour les tests depuis le navigateur.
    """
    try:
        result = get_video_info(url)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": str(e)},
        )
    except Exception as e:
        logger.exception("Erreur inattendue dans video_info_get")
        raise HTTPException(
            status_code=500,
            detail={"error": "Une erreur interne est survenue", "detail": str(e)},
        )


@router.post(
    "/video/download/async",
    response_model=DownloadStartResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Requête invalide"},
        500: {"model": ErrorResponse, "description": "Erreur serveur"},
    },
    summary="Lancer un téléchargement asynchrone",
    description=(
        "Lance le téléchargement d'une vidéo en arrière-plan et retourne "
        "un identifiant de tâche (task_id) pour suivre la progression "
        "via l'endpoint GET /video/download/async/{task_id}/progress."
    ),
)
async def video_download_async(request: VideoDownloadRequest):
    """
    Endpoint POST /api/v1/video/download/async

    Lance le téléchargement en arrière-plan et retourne immédiatement
    un task_id pour suivre la progression.
    """
    try:
        task_id = start_async_download(request.url, request.format)
        return DownloadStartResponse(task_id=task_id, status="pending")
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": str(e)},
        )
    except Exception as e:
        logger.exception("Erreur inattendue dans video_download_async")
        raise HTTPException(
            status_code=500,
            detail={"error": "Une erreur interne est survenue", "detail": str(e)},
        )


@router.get(
    "/video/download/async/{task_id}/progress",
    response_model=DownloadProgressResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Tâche introuvable"},
        500: {"model": ErrorResponse, "description": "Erreur serveur"},
    },
    summary="Suivre la progression d'un téléchargement",
    description=(
        "Retourne l'état d'avancement d'un téléchargement asynchrone "
        "lancé via POST /video/download/async."
    ),
)
async def video_download_progress(task_id: str):
    """
    Endpoint GET /api/v1/video/download/async/{task_id}/progress

    Retourne la progression en temps réel :
    - status : pending / downloading / processing / completed / error
    - progress : pourcentage (0-100)
    - speed : vitesse de téléchargement (ex: "2.5 MiB/s")
    - eta : temps restant estimé en secondes
    - filename : nom du fichier (une fois terminé)
    """
    task = get_progress(task_id)
    if task is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "Tâche introuvable", "detail": f"Aucune tâche avec l'id {task_id}"},
        )

    return task.to_dict()


@router.get(
    "/video/download/async/{task_id}/file",
    responses={
        404: {"model": ErrorResponse, "description": "Tâche ou fichier introuvable"},
        400: {"model": ErrorResponse, "description": "Téléchargement pas encore terminé"},
        500: {"model": ErrorResponse, "description": "Erreur serveur"},
    },
    summary="Récupérer le fichier téléchargé",
    description=(
        "Une fois le téléchargement terminé (status=completed), "
        "cet endpoint retourne le fichier téléchargé."
    ),
)
async def video_download_file(task_id: str):
    """
    Endpoint GET /api/v1/video/download/async/{task_id}/file

    Retourne le fichier une fois que le téléchargement est terminé.
    """
    task = get_progress(task_id)
    if task is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "Tâche introuvable"},
        )

    if task.status != DownloadStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Téléchargement pas encore terminé",
                "detail": f"Statut actuel : {task.status.value}",
            },
        )

    filepath = get_task_file_path(task_id)
    if filepath is None or not filepath.exists():
        raise HTTPException(
            status_code=404,
            detail={"error": "Fichier introuvable sur le serveur"},
        )

    media_type = (
        "audio/mpeg" if task.output_format == "mp3" else "video/mp4"
    )

    return FileResponse(
        path=filepath,
        media_type=media_type,
        filename=filepath.name,
        headers={
            "Content-Disposition": f'attachment; filename="{filepath.name}"',
        },
    )


@router.get(
    "/health",
    summary="Vérification de santé du service",
    description="Endpoint simple pour vérifier que l'API est opérationnelle.",
)
async def health_check():
    """Retourne l'état de santé de l'API."""
    return {
        "status": "healthy",
        "service": "StreamGrab API",
        "version": "1.0.0",
    }
