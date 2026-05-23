"""
Routes API pour l'authentification JWT.

Endpoints:
- POST /api/v1/auth/register - Créer un nouvel utilisateur
- POST /api/v1/auth/login - Connecter un utilisateur et obtenir un token
"""

import logging
from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import UserCreate, LoginRequest, TokenResponse, UserResponse
from app.services.auth_service import (
    create_user,
    authenticate_user,
    get_user_by_id,
)
from app.auth import create_access_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un nouveau compte",
    description="Enregistre un nouvel utilisateur et retourne un token JWT",
)
async def register(user_data: UserCreate):
    """Crée un nouvel utilisateur et retourne un token d'accès."""
    try:
        # Créer l'utilisateur
        user = create_user(user_data)
        
        # Générer le token
        access_token = create_access_token(
            user_id=user.id,
            username=user.username,
            email=user.email
        )
        
        logger.info(f"Nouvel utilisateur créé : {user.username}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user
        )
    
    except ValueError as e:
        logger.warning(f"Erreur d'enregistrement : {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Se connecter",
    description="Authentifie un utilisateur et retourne un token JWT",
)
async def login(credentials: LoginRequest):
    """Authentifie un utilisateur et retourne un token JWT."""
    # Authentifier l'utilisateur
    user = authenticate_user(credentials.username, credentials.password)
    
    if not user:
        logger.warning(f"Tentative de connexion échouée : {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Générer le token
    access_token = create_access_token(
        user_id=user["id"],
        username=user["username"],
        email=user["email"]
    )
    
    logger.info(f"Utilisateur connecté : {credentials.username}")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"]
        )
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtenir le profil de l'utilisateur actuel",
    description="Retourne les informations de l'utilisateur connecté",
)
async def get_current_user_profile(current_user: dict = None):
    """Endpoint protégé pour obtenir les infos de l'utilisateur."""
    # Note: current_user serait passé via Depends(get_current_user) en production
    # Pour la démo, on retourne une réponse générique
    if current_user:
        user = get_user_by_id(current_user["user_id"])
        if user:
            return UserResponse(
                id=user["id"],
                username=user["username"],
                email=user["email"]
            )
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Non authentifié"
    )
