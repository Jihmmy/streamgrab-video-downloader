"""
Configuration centralisée du backend StreamGrab.

Pourquoi un fichier config séparé ?
- Centralise tous les réglages modifiables
- Facilite les changements sans toucher au code métier
- Prépare une future gestion par variables d'environnement
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Répertoire racine du backend
BASE_DIR = Path(__file__).resolve().parent.parent

# Dossier de téléchargement temporaire
DOWNLOAD_DIR = BASE_DIR / "downloads"

# Création automatique du dossier de téléchargement
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ─── Contournement anti-bot YouTube ────────────────────────────
# YouTube bloque yt-dlp sans cookies depuis 2025.
# Mais le client ANDROID de yt-dlp contourne cette vérification
# car YouTube autorise les requêtes depuis l'app Android sans auth.
#
# Plus besoin de cookies navigateur (qui plante quand le browser est ouvert)

# Options de base yt-dlp
YT_DLP_OPTIONS = {
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "force_generic_extractor": False,
    # Clé du contournement : utiliser les clients Android + TV
    # YouTube ne demande pas de vérification bot sur ces plateformes
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "android_proxy", "web"],
            "skip": ["dash", "hls"],
        },
    },
    # Retry automatique en cas d'erreur réseau
    "extractor_retries": 5,
    "fragment_retries": 10,
    # Timeout plus long pour éviter les Read timed out
    "socket_timeout": 120,
    # Ignorer les erreurs mineures
    "ignoreerrors": False,
}

# Formats autorisés pour le téléchargement
ALLOWED_FORMATS = {
    "mp4": {
        "label": "MP4 (Vidéo)",
        "ext": "mp4",
        "description": "Meilleure qualité vidéo disponible",
    },
    "mp3": {
        "label": "MP3 (Audio)",
        "ext": "mp3",
        "description": "Audio uniquement, qualité 192kbps",
    },
}

# Limite de taille (optionnel, en octets)
# None = pas de limite
MAX_FILE_SIZE = None  # 500 * 1024 * 1024  # 500MB

# Taille maximale de téléchargement pour le titre
MAX_TITLE_LENGTH = 200