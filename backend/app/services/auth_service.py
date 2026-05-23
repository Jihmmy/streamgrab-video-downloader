"""
Service de gestion des utilisateurs.

Note: Ceci est une implémentation simple avec stockage en mémoire.
En production, intégrer une vraie base de données (PostgreSQL, etc.)
"""

from typing import Optional, Dict
from app.auth import hash_password, verify_password
from app.schemas.auth import UserCreate, UserResponse, SocialLoginRequest

# Base de données en mémoire (simulée)
users_db: Dict[int, dict] = {}
next_user_id: int = 1


def create_user(user_create: UserCreate) -> UserResponse:
    """Crée un nouvel utilisateur."""
    global next_user_id
    
    # Vérifier que l'email n'existe pas
    for user in users_db.values():
        if user["email"] == user_create.email or user["username"] == user_create.username:
            raise ValueError("Email ou username déjà utilisé")
    
    user_id = next_user_id
    next_user_id += 1
    
    user_data = {
        "id": user_id,
        "email": user_create.email,
        "username": user_create.username,
        "hashed_password": hash_password(user_create.password),
        "provider": None,  # compte classique
    }
    
    users_db[user_id] = user_data
    return UserResponse(id=user_data["id"], email=user_data["email"], username=user_data["username"])


def get_user_by_email(email: str) -> Optional[dict]:
    """Récupère un utilisateur par son email."""
    for user in users_db.values():
        if user["email"] == email:
            return user
    return None


def create_or_get_social_user(provider: str, email: str, name: str) -> UserResponse:
    """
    Crée ou récupère un utilisateur via un fournisseur OAuth (Google / Facebook).
    
    Si l'email existe déjà, on retourne l'utilisateur existant.
    Sinon, on crée un nouvel utilisateur avec un mot de passe aléatoire (jamais utilisé).
    """
    global next_user_id

    existing = get_user_by_email(email)
    if existing:
        return UserResponse(id=existing["id"], email=existing["email"], username=existing["username"])

    user_id = next_user_id
    next_user_id += 1

    # Générer un username à partir du nom + suffixe si besoin
    username_base = name.replace(" ", "_").lower()
    username = username_base
    suffix = 1
    while any(u["username"] == username for u in users_db.values()):
        username = f"{username_base}_{suffix}"
        suffix += 1

    user_data = {
        "id": user_id,
        "email": email,
        "username": username,
        "hashed_password": None,  # pas de mot de passe pour les comptes sociaux
        "provider": provider,
    }

    users_db[user_id] = user_data
    return UserResponse(id=user_data["id"], email=user_data["email"], username=user_data["username"])


def get_user_by_username(username: str) -> Optional[dict]:
    """Récupère un utilisateur par son nom d'utilisateur."""
    for user in users_db.values():
        if user["username"] == username:
            return user
    return None


def get_user_by_id(user_id: int) -> Optional[dict]:
    """Récupère un utilisateur par son ID."""
    return users_db.get(user_id)


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authentifie un utilisateur.
    
    Returns:
        Les données de l'utilisateur si l'authentification est réussie, None sinon
    """
    user = get_user_by_username(username)
    if not user:
        return None
    
    if not verify_password(password, user["hashed_password"]):
        return None
    
    return user
