"""
Point d'entrée principal de l'API StreamGrab.

Pourquoi ce fichier ?
- Initialise l'application FastAPI
- Configure CORS (indispensable pour le frontend React)
- Enregistre les routers
- Configure le logging
- Fournit des événements de cycle de vie (startup/shutdown)
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import DOWNLOAD_DIR
from app.routers.video import router as video_router

# Configuration du logging avec support UTF-8
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)

# Forcer UTF-8 pour stdout/stderr (évite les problèmes d'accents)
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le cycle de vie de l'application.

    Startup :
    - Vérifie que le dossier de téléchargement existe
    - Log le démarrage

    Shutdown :
    - Log l'arrêt
    """
    # Startup
    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("=" * 50)
    logger.info("StreamGrab API démarrée")
    logger.info(f"Dossier de téléchargement : {DOWNLOAD_DIR}")
    logger.info("=" * 50)

    yield

    # Shutdown
    logger.info("StreamGrab API arrêtée")


# Création de l'application FastAPI
app = FastAPI(
    title="StreamGrab API",
    description=(
        "API de téléchargement et d'analyse de vidéos en ligne.\n\n"
        "Fonctionnalités :\n"
        "- Analyse d'une vidéo à partir de son URL\n"
        "- Téléchargement au format MP4 (vidéo) ou MP3 (audio)\n"
        "- Classification intelligente des formats disponibles"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc UI
)

# Configuration CORS
# Autorise le frontend React (qui tourne en général sur http://localhost:5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Next.js dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrement des routers
app.include_router(video_router)


@app.get("/")
async def root():
    """
    Racine de l'API.
    Redirige vers la documentation Swagger.
    """
    return {
        "message": "Bienvenue sur StreamGrab API",
        "documentation": "/docs",
        "health": "/api/v1/health",
        "version": "1.0.0",
    }