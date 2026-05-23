"""
Logique d'authentification JWT.

Responsabilités:
- Hasher les mots de passe avec bcrypt
- Générer les tokens JWT
- Vérifier et décoder les tokens JWT
- Gérer les clés secrètes
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-12345678")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Contexte pour hasher les mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Schéma de sécurité
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash un mot de passe avec bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si un mot de passe correspond au hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: int,
    username: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Crée un token JWT.
    
    Args:
        user_id: ID de l'utilisateur
        username: Nom d'utilisateur
        email: Email de l'utilisateur
        expires_delta: Durée d'expiration personnalisée (optionnel)
    
    Returns:
        Token JWT encodé
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode = {
        "user_id": user_id,
        "username": username,
        "email": email,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> dict:
    """
    Décode et valide un token JWT.
    
    Args:
        token: Token JWT à décoder
    
    Returns:
        Dictionnaire contenant les données du token
    
    Raises:
        HTTPException: Si le token est invalide ou expiré
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        username: str = payload.get("username")
        email: str = payload.get("email")
        
        if user_id is None or username is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token invalide : données manquantes",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return {"user_id": user_id, "username": username, "email": email}
    
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Dépendance FastAPI pour obtenir l'utilisateur actuel.
    Utilise le token Bearer JWT.
    """
    token = credentials.credentials
    return decode_access_token(token)
