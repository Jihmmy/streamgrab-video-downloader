"""
Routes API pour l'authentification JWT et OAuth.

Endpoints:
- POST /api/v1/auth/register - Créer un nouvel utilisateur
- POST /api/v1/auth/login - Connecter un utilisateur et obtenir un token
- POST /api/v1/auth/social - Connecter via OAuth (Google / Facebook)
"""

import logging
import os
from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import UserCreate, LoginRequest, SocialLoginRequest, TokenResponse, UserResponse
from app.services.auth_service import (
    create_user,
    authenticate_user,
    get_user_by_id,
    create_or_get_social_user,
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
        user = create_user(user_data)
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
    user = authenticate_user(credentials.username, credentials.password)
    if not user:
        logger.warning(f"Tentative de connexion échouée : {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides",
            headers={"WWW-Authenticate": "Bearer"},
        )
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


@router.post(
    "/social",
    response_model=TokenResponse,
    summary="Se connecter avec Google / Facebook",
    description="Authentifie un utilisateur via un token OAuth (Google ou Facebook)",
)
async def social_login(request: SocialLoginRequest):
    """
    Reçoit un token ID provenant de Google ou Facebook,
    le vérifie côté serveur, puis crée ou connecte l'utilisateur.
    """
    try:
        payload = None

        if request.provider == "google":
            payload = verify_google_token(request.token)
        elif request.provider == "facebook":
            payload = verify_facebook_token(request.token)
        else:
            raise ValueError(f"Fournisseur inconnu : {request.provider}")

        email = payload.get("email")
        name = payload.get("name", email.split("@")[0])

        if not email:
            raise ValueError("L'email est requis pour l'authentification sociale")

        user = create_or_get_social_user(request.provider, email, name)

        access_token = create_access_token(
            user_id=user.id,
            username=user.username,
            email=user.email,
        )

        logger.info(f"Connexion sociale réussie : {user.username} via {request.provider}")
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Erreur lors de l'authentification sociale")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token social invalide ou expiré",
        )


def verify_google_token(token: str) -> dict:
    """
    Vérifie un token ID Google et retourne les claims (email, name, ...).
    Utilise la bibliothèque google-auth officielle.
    """
    from google.oauth2 import id_token
    from google.auth.transport import requests

    google_client_id = os.getenv("GOOGLE_CLIENT_ID")

    if not google_client_id:
        # Mode développement / fallback : décoder sans vérifier la signature
        # (permet de tester sans clé Google)
        import json, base64
        parts = token.split(".")
        if len(parts) == 3:
            try:
                # Padding pour base64
                payload_b64 = parts[1]
                payload_b64 += "=" * (4 - len(payload_b64) % 4)
                decoded = base64.urlsafe_b64decode(payload_b64)
                claims = json.loads(decoded)
                if "email" in claims:
                    return claims
            except Exception:
                pass
        raise ValueError("Token Google invalide (mode fallback)")

    try:
        info = id_token.verify_oauth2_token(token, requests.Request(), google_client_id)
        if info.get("iss") not in ["accounts.google.com", "https://accounts.google.com"]:
            raise ValueError("Mauvais émetteur du token Google")
        return info
    except ValueError as e:
        raise ValueError(f"Token Google invalide : {str(e)}")


def verify_facebook_token(token: str) -> dict:
    """
    Vérifie un token Facebook (App Access Token) et retourne les claims.
    Appelle l'API Graph de Facebook.
    """
    import requests as http_requests

    fb_app_id = os.getenv("FACEBOOK_APP_ID")
    fb_app_secret = os.getenv("FACEBOOK_APP_SECRET")

    if not fb_app_id or not fb_app_secret:
        # Mode développement / fallback : décoder sans vérifier
        import json, base64
        parts = token.split(".")
        if len(parts) == 3:
            try:
                payload_b64 = parts[1]
                payload_b64 += "=" * (4 - len(payload_b64) % 4)
                decoded = base64.urlsafe_b64decode(payload_b64)
                claims = json.loads(decoded)
                if "email" in claims:
                    return claims
            except Exception:
                pass
        raise ValueError("Token Facebook invalide (mode fallback)")

    # Vérification via Facebook Graph API
    url = f"https://graph.facebook.com/debug_token?input_token={token}&access_token={fb_app_id}|{fb_app_secret}"
    resp = http_requests.get(url)
    data = resp.json()

    if "error" in data:
        raise ValueError(f"Token Facebook invalide : {data['error'].get('message', 'erreur inconnue')}")

    # Récupérer les infos utilisateur
    user_url = f"https://graph.facebook.com/me?fields=id,name,email&access_token={token}"
    user_resp = http_requests.get(user_url)
    user_data = user_resp.json()

    if "email" not in user_data:
        raise ValueError("Impossible de récupérer l'email depuis Facebook")

    return {
        "email": user_data["email"],
        "name": user_data.get("name", user_data.get("email", "").split("@")[0]),
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtenir le profil de l'utilisateur actuel",
    description="Retourne les informations de l'utilisateur connecté",
)
async def get_current_user_profile(current_user: dict = None):
    """Endpoint protégé pour obtenir les infos de l'utilisateur."""
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