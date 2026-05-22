"""
Service métier pour l'analyse et le téléchargement de vidéos.

Pourquoi un service séparé ?
- Sépare la logique métier des routes API (principe de responsabilité unique)
- Facile à tester unitairement
- Réutilisable depuis différents endpoints
- Si on change yt-dlp pour une autre lib, on ne modifie qu'ici
"""

import re
import subprocess
import logging
import time
from pathlib import Path
from typing import Optional
import yt_dlp

from app.config import DOWNLOAD_DIR, YT_DLP_OPTIONS, ALLOWED_FORMATS
from app.schemas.video import VideoInfoResponse, FormatInfo

logger = logging.getLogger(__name__)

# Nombre de tentatives pour les timeouts réseau
MAX_RETRIES = 3
RETRY_BACKOFF = 5  # secondes, doublé à chaque tentative


def _retry_on_timeout(func, *args, **kwargs):
    """
    Ré-exécute func en cas d'erreur timeout réseau.
    Backoff exponentiel entre chaque tentative.
    """
    last_exception = None
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except (yt_dlp.utils.DownloadError, OSError) as e:
            error_msg = str(e).lower()
            is_timeout = (
                "read timed out" in error_msg
                or "timeout" in error_msg
                or "connection reset" in error_msg
                or "connection refused" in error_msg
                or "no route to host" in error_msg
            )
            if is_timeout and attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF * (2 ** attempt)
                logger.warning(
                    f"Timeout réseau (tentative {attempt + 1}/{MAX_RETRIES}), "
                    f"nouvelle tentative dans {wait}s : {e}"
                )
                time.sleep(wait)
                last_exception = e
            else:
                raise
    raise last_exception  # ne devrait jamais arriver, mais sécurité


def _format_duration(seconds: Optional[int]) -> Optional[str]:
    """Convertit des secondes en format mm:ss ou hh:mm:ss."""
    if seconds is None:
        return None
    hours, remainder = divmod(int(seconds), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _is_url_valid(url: str) -> bool:
    """
    Vérifie rapidement si l'URL a un format plausible.
    Évite d'appeler yt-dlp pour des URLs invalides.
    """
    pattern = re.compile(
        r"^https?://"  # http:// ou https://
        r"[\w\-._~:/?#\[\]@!$&'()*+,;=]+"  # caractères autorisés dans une URL
        r"\.[\w\-]+"  # domaine (.com, .org, etc.)
        r"[\w\-._~:/?#\[\]@!$&'()*+,;=]*$"  # reste de l'URL
    )
    return bool(pattern.match(url))


def get_video_info(url: str) -> VideoInfoResponse:
    """
    Analyse une vidéo et retourne ses métadonnées + formats disponibles.

    Utilise yt-dlp en mode extraction uniquement (pas de téléchargement).
    """
    if not _is_url_valid(url):
        raise ValueError("L'URL fournie n'est pas valide.")

    options = {
        **YT_DLP_OPTIONS,
        "no_download": True,  # ⚡ Extraction uniquement, pas de téléchargement
    }

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            logger.info(f"Analyse de la vidéo : {url}")
            info = _retry_on_timeout(ydl.extract_info, url, download=False)

            if info is None:
                raise ValueError("Impossible d'extraire les informations de la vidéo.")

            # Analyse et classification des formats disponibles
            formats: list[FormatInfo] = []
            has_mp4_video = False
            has_audio_for_mp3 = False

            for fmt in info.get("formats", []):
                # Ne garder que les formats utiles
                ext = fmt.get("ext", "")
                vcodec = fmt.get("vcodec", "none")
                acodec = fmt.get("acodec", "none")

                has_video = vcodec != "none"
                has_audio = acodec != "none"

                # Déterminer si compatible MP4 (h264 video + aac/mp4a audio)
                is_mp4_compatible = (
                    ext == "mp4"
                    and has_video
                    and ("h264" in str(vcodec).lower() or "avc1" in str(vcodec).lower())
                )
                if is_mp4_compatible:
                    has_mp4_video = True

                # Format audio uniquement pour MP3
                if (
                    has_audio
                    and not has_video
                    and ext in ("m4a", "webm")
                ):
                    has_audio_for_mp3 = True

                # Calcul de la taille en Mo
                filesize = fmt.get("filesize") or fmt.get("filesize_approx")
                filesize_mb = round(filesize / (1024 * 1024), 2) if filesize else None

                # Label de qualité
                quality = None
                height = fmt.get("height")
                if height:
                    quality = f"{height}p"
                    fps = fmt.get("fps")
                    if fps:
                        quality += f" {fps}fps"
                elif fmt.get("abr"):
                    quality = f"{fmt['abr']}kbps"
                elif fmt.get("tbr"):
                    quality = f"{fmt['tbr']:.0f}kbps"

                format_info = FormatInfo(
                    format_id=fmt.get("format_id", "unknown"),
                    ext=ext,
                    quality=quality,
                    filesize=filesize,
                    filesize_mb=filesize_mb,
                    has_audio=has_audio,
                    has_video=has_video,
                    is_mp4_compatible=is_mp4_compatible,
                    is_mp3_compatible=(has_audio and not has_video),
                )
                formats.append(format_info)

            # Déterminer les formats de sortie disponibles
            available_formats = []
            if has_mp4_video:
                available_formats.append("mp4")
            if has_audio_for_mp3 or any(f.is_mp3_compatible for f in formats):
                available_formats.append("mp3")

            # Fallback : si aucun format spécifique détecté mais formats existent
            if not available_formats and formats:
                available_formats = ["mp4"]

            # Construire la réponse
            response = VideoInfoResponse(
                title=info.get("title", "Sans titre"),
                duration=info.get("duration"),
                duration_formatted=_format_duration(info.get("duration")),
                thumbnail=info.get("thumbnail"),
                webpage_url=url,
                uploader=info.get("uploader") or info.get("channel"),
                upload_date=info.get("upload_date"),
                description=info.get("description", "")[:500],  # Limiter la description
                formats=formats,
                available_formats=available_formats,
            )

            logger.info(f"Vidéo analysée avec succès : {response.title}")
            return response

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        logger.error(f"Erreur yt-dlp lors de l'analyse : {error_msg}")
        
        # Message clair pour l'erreur YouTube
        if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
            raise ValueError(
                "YouTube demande une vérification anti-bot. "
                "Le client Android est utilisé pour contourner, "
                "mais YouTube peut encore bloquer selon la vidéo."
            ) from e
        
        raise ValueError(
            f"Impossible d'analyser cette vidéo : {error_msg[:200]}"
        ) from e
    except Exception as e:
        logger.error(f"Erreur inattendue lors de l'analyse : {e}")
        raise ValueError(f"Erreur lors de l'analyse de la vidéo : {str(e)}") from e


def download_video(url: str, output_format: str) -> Path:
    """
    Télécharge une vidéo et la convertit dans le format demandé.

    Args:
        url: URL de la vidéo
        output_format: "mp4" (vidéo) ou "mp3" (audio)

    Returns:
        Chemin vers le fichier téléchargé

    Format MP4 :
        - Meilleure qualité vidéo + audio combinés
        - Re-encode si nécessaire en h264 + aac

    Format MP3 :
        - Extrait l'audio uniquement
        - Convertit en MP3 qualité 192kbps
    """
    if output_format not in ALLOWED_FORMATS:
        raise ValueError(f"Format non supporté : {output_format}")

    if not _is_url_valid(url):
        raise ValueError("L'URL fournie n'est pas valide.")

    # Nom de fichier temporaire avec timestamp pour éviter les collisions
    output_template = str(DOWNLOAD_DIR / f"%(title)s_%(id)s.%(ext)s")

    # Options de base
    options = {
        **YT_DLP_OPTIONS,
        "outtmpl": output_template,
        "restrictfilenames": True,  # Évite les caractères problématiques
    }

    if output_format == "mp4":
        # MP4 : meilleure qualité vidéo + audio
        options.update({
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
        })
    elif output_format == "mp3":
        # MP3 : extraire l'audio uniquement
        options.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "postprocessor_args": [
                "-id3v2_version", "3",
            ],
        })

    try:
        logger.info(f"Téléchargement de la vidéo : {url} (format: {output_format})")

        with yt_dlp.YoutubeDL(options) as ydl:
            info = _retry_on_timeout(ydl.extract_info, url, download=True)

            if info is None:
                raise ValueError("Impossible de télécharger la vidéo.")

            # Le chemin du fichier final
            title = info.get("title", "video")
            video_id = info.get("id", "unknown")

            if output_format == "mp3":
                filename = f"{title}_{video_id}.mp3"
            else:
                filename = f"{title}_{video_id}.mp4"

            # Nettoyer le nom de fichier
            filename = "".join(c for c in filename if c.isalnum() or c in "._- ").strip()
            filepath = DOWNLOAD_DIR / filename

            # Vérifier que le fichier existe
            if not filepath.exists():
                # Chercher un fichier similaire
                existing_files = list(DOWNLOAD_DIR.glob(f"*{video_id}*"))
                if existing_files:
                    filepath = existing_files[0]
                else:
                    raise FileNotFoundError(
                        f"Le fichier téléchargé est introuvable : {filepath}"
                    )

            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            logger.info(
                f"Téléchargement réussi : {filepath.name} "
                f"({file_size_mb:.1f} Mo)"
            )

            return filepath

    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        logger.error(f"Erreur yt-dlp lors du téléchargement : {error_msg}")
        
        if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
            raise ValueError(
                "YouTube bloque le téléchargement (vérification anti-bot). "
                "Utilisation du client Android pour contourner."
            ) from e
        
        if "read timed out" in error_msg.lower() or "timeout" in error_msg.lower():
            raise ValueError(
                "Le téléchargement a échoué après plusieurs tentatives : "
                "timeout réseau. Vérifiez votre connexion Internet et réessayez."
            ) from e
        
        raise ValueError(
            f"Impossible de télécharger la vidéo : {error_msg[:200]}"
        ) from e
    except Exception as e:
        logger.error(f"Erreur inattendue lors du téléchargement : {e}")
        raise ValueError(f"Erreur lors du téléchargement : {str(e)}") from e


def cleanup_downloads(max_age_hours: int = 1):
    """
    Nettoie les fichiers téléchargés plus vieux que max_age_hours.
    À appeler périodiquement ou après chaque téléchargement.
    """
    import time

    now = time.time()
    cleaned = 0
    for filepath in DOWNLOAD_DIR.iterdir():
        if filepath.is_file():
            file_age_hours = (now - filepath.stat().st_mtime) / 3600
            if file_age_hours > max_age_hours:
                filepath.unlink()
                cleaned += 1

    if cleaned > 0:
        logger.info(f"Nettoyage : {cleaned} fichier(s) supprimé(s)")