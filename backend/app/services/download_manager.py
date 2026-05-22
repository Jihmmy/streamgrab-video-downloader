"""
Gestionnaire de téléchargements asynchrones avec suivi de progression.

Pourquoi un module séparé ?
- Centralise la gestion des tâches de téléchargement
- Permet le suivi en temps réel via des WebSockets ou polling
- Thread-safe pour les accès concurrents
- Nettoyage automatique des tâches expirées
"""

import uuid
import time
import threading
import logging
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass, field
from enum import Enum

import yt_dlp

from app.config import DOWNLOAD_DIR, YT_DLP_OPTIONS, ALLOWED_FORMATS

logger = logging.getLogger(__name__)

# ─── Modèles ─────────────────────────────────────────────────────


class DownloadStatus(str, Enum):
    """Statuts possibles d'une tâche de téléchargement."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"  # Post-processing (conversion MP3, etc.)
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class DownloadTask:
    """Représente une tâche de téléchargement avec son état."""
    task_id: str
    url: str
    output_format: str
    status: DownloadStatus = DownloadStatus.PENDING
    progress: float = 0.0  # 0.0 à 100.0
    filename: Optional[str] = None
    filepath: Optional[Path] = None
    error: Optional[str] = None
    speed: Optional[str] = None
    eta: Optional[int] = None
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour l'API JSON."""
        return {
            "task_id": self.task_id,
            "url": self.url,
            "format": self.output_format,
            "status": self.status.value,
            "progress": round(self.progress, 1),
            "filename": self.filename,
            "error": self.error,
            "speed": self.speed,
            "eta": self.eta,
        }


# ─── Stockage thread-safe ────────────────────────────────────────

_tasks: Dict[str, DownloadTask] = {}
_lock = threading.Lock()
CLEANUP_INTERVAL = 300  # 5 minutes
TASK_MAX_AGE = 1800  # 30 minutes


def _cleanup_old_tasks():
    """Supprime les tâches terminées ou en erreur de plus de TASK_MAX_AGE secondes."""
    now = time.time()
    with _lock:
        expired = [
            tid for tid, task in _tasks.items()
            if task.status in (DownloadStatus.COMPLETED, DownloadStatus.ERROR)
            and (now - task.created_at) > TASK_MAX_AGE
        ]
        for tid in expired:
            del _tasks[tid]
        if expired:
            logger.info(f"Nettoyage : {len(expired)} tâche(s) expirée(s) supprimée(s)")


# ─── Progress hook yt-dlp ────────────────────────────────────────


def _make_progress_hook(task_id: str):
    """
    Crée un hook de progression pour yt-dlp qui met à jour la tâche.

    yt-dlp appelle ce hook régulièrement pendant le téléchargement :
    - status='downloading' → mise à jour de la progression
    - status='finished' → téléchargement terminé (post-processing commence)
    - status='error' → erreur
    """
    def hook(d: dict):
        with _lock:
            task = _tasks.get(task_id)
            if task is None:
                return

            status = d.get("status", "")

            if status == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded = d.get("downloaded_bytes", 0)
                if total > 0:
                    task.progress = min(95.0, (downloaded / total) * 100.0)
                task.status = DownloadStatus.DOWNLOADING

                # Infos de vitesse et ETA
                speed = d.get("_speed_str")
                if speed:
                    task.speed = speed
                eta = d.get("_eta")
                if eta is not None:
                    task.eta = int(eta)

            elif status == "finished":
                # Téléchargement terminé, post-processing en cours
                task.progress = 95.0
                task.status = DownloadStatus.PROCESSING

            elif status == "error":
                task.status = DownloadStatus.ERROR
                task.error = d.get("error", "Erreur inconnue pendant le téléchargement")

            logger.debug(
                f"Progress [{task_id}] : {task.progress:.1f}% | "
                f"status={task.status.value} | speed={task.speed} | eta={task.eta}"
            )

    return hook


# ─── Fonctions de service ────────────────────────────────────────


def start_download(url: str, output_format: str) -> str:
    """
    Lance un téléchargement en arrière-plan.

    Args:
        url: URL de la vidéo
        output_format: "mp4" ou "mp3"

    Returns:
        task_id: Identifiant unique pour suivre la progression

    La fonction retourne immédiatement. Le téléchargement s'effectue
    dans un thread séparé. Utilisez get_progress(task_id) pour suivre
    l'avancement.
    """
    if output_format not in ALLOWED_FORMATS:
        raise ValueError(f"Format non supporté : {output_format}")

    # Créer la tâche
    task_id = str(uuid.uuid4())
    task = DownloadTask(
        task_id=task_id,
        url=url,
        output_format=output_format,
    )

    with _lock:
        _tasks[task_id] = task

    # Lancer le téléchargement dans un thread séparé
    thread = threading.Thread(
        target=_do_download,
        args=(task_id,),
        daemon=True,
        name=f"download-{task_id[:8]}",
    )
    thread.start()

    # Nettoyage périodique
    _cleanup_old_tasks()

    logger.info(f"Tâche créée : {task_id} ({url}, {output_format})")
    return task_id


def get_progress(task_id: str) -> Optional[DownloadTask]:
    """
    Récupère l'état d'avancement d'un téléchargement.

    Args:
        task_id: Identifiant de la tâche

    Returns:
        DownloadTask ou None si la tâche n'existe pas
    """
    with _lock:
        task = _tasks.get(task_id)
        if task is None:
            return None
        # Retourner une copie pour éviter les modifications concurrentes
        import copy
        return copy.copy(task)


def get_task_file_path(task_id: str) -> Optional[Path]:
    """
    Retourne le chemin du fichier téléchargé si la tâche est terminée.

    Args:
        task_id: Identifiant de la tâche

    Returns:
        Path du fichier ou None
    """
    with _lock:
        task = _tasks.get(task_id)
        if task and task.status == DownloadStatus.COMPLETED and task.filepath:
            return task.filepath
        return None


# ─── Fonction interne de téléchargement ──────────────────────────


def _do_download(task_id: str):
    """
    Exécute le téléchargement dans un thread séparé.

    Cette fonction est appelée par start_download() dans un thread daemon.
    Elle met à jour la tâche au fur et à mesure via le progress hook.
    """
    task = _tasks.get(task_id)
    if task is None:
        return

    url = task.url
    output_format = task.output_format

    # Template de sortie
    output_template = str(DOWNLOAD_DIR / f"%(title)s_%(id)s.%(ext)s")

    # Options de base
    options = {
        **YT_DLP_OPTIONS,
        "outtmpl": output_template,
        "restrictfilenames": True,
        "progress_hooks": [_make_progress_hook(task_id)],
    }

    if output_format == "mp4":
        options.update({
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "merge_output_format": "mp4",
        })
    elif output_format == "mp3":
        options.update({
            "format": "bestaudio/best",
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }],
            "postprocessor_args": ["-id3v2_version", "3"],
        })

    try:
        logger.info(f"Début du téléchargement [{task_id}] : {url} ({output_format})")

        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)

            if info is None:
                raise ValueError("Impossible de télécharger la vidéo.")

            # Déterminer le nom du fichier final
            title = info.get("title", "video")
            video_id = info.get("id", "unknown")

            if output_format == "mp3":
                filename = f"{title}_{video_id}.mp3"
            else:
                filename = f"{title}_{video_id}.mp4"

            # Nettoyer le nom
            filename = "".join(c for c in filename if c.isalnum() or c in "._- ").strip()
            filepath = DOWNLOAD_DIR / filename

            # Vérifier l'existence du fichier
            if not filepath.exists():
                existing = list(DOWNLOAD_DIR.glob(f"*{video_id}*"))
                if existing:
                    filepath = existing[0]
                else:
                    raise FileNotFoundError(
                        f"Fichier introuvable après téléchargement : {filepath}"
                    )

            # Mettre à jour la tâche
            with _lock:
                task = _tasks.get(task_id)
                if task:
                    task.status = DownloadStatus.COMPLETED
                    task.progress = 100.0
                    task.filename = filepath.name
                    task.filepath = filepath
                    task.speed = None
                    task.eta = None

            file_size_mb = filepath.stat().st_size / (1024 * 1024)
            logger.info(
                f"Téléchargement réussi [{task_id}] : {filepath.name} "
                f"({file_size_mb:.1f} Mo)"
            )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Erreur lors du téléchargement [{task_id}] : {error_msg}")

        with _lock:
            task = _tasks.get(task_id)
            if task:
                task.status = DownloadStatus.ERROR
                task.error = str(e)[:500]
                task.progress = 0.0