"""
Schémas Pydantic pour l'authentification JWT et OAuth.
"""

from pydantic import BaseModel, Field
from typing import Optional


class UserBase(BaseModel):
    """Données de base d'un utilisateur."""
    email: str = Field(..., description="Adresse email de l'utilisateur")
    username: str = Field(..., min_length=3, description="Nom d'utilisateur")


class UserCreate(UserBase):
    """Schéma pour créer un nouvel utilisateur."""
    password: str = Field(..., min_length=8, description="Mot de passe (minimum 8 caractères)")


class UserResponse(UserBase):
    """Schéma de réponse pour un utilisateur."""
    id: int = Field(..., description="ID unique de l'utilisateur")
    
    class Config:
        from_attributes = True


class TokenData(BaseModel):
    """Données contenues dans le token JWT."""
    user_id: int = Field(..., description="ID de l'utilisateur")
    username: str = Field(..., description="Nom d'utilisateur")
    email: str = Field(..., description="Email de l'utilisateur")


class TokenResponse(BaseModel):
    """Réponse avec le token JWT."""
    access_token: str = Field(..., description="Token JWT")
    token_type: str = Field(default="bearer", description="Type de token")
    user: UserResponse = Field(..., description="Données de l'utilisateur")


class LoginRequest(BaseModel):
    """Requête de connexion."""
    username: str = Field(..., description="Nom d'utilisateur")
    password: str = Field(..., description="Mot de passe")


class SocialLoginRequest(BaseModel):
    """Requête de connexion via OAuth (Google / Facebook)."""
    provider: str = Field(..., description="Fournisseur OAuth: 'google' ou 'facebook'")
    token: str = Field(..., description="Token ID renvoyé par le fournisseur OAuth")