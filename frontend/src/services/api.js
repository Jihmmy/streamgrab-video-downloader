/**
 * Service API StreamGrab
 * 
 * Centralise tous les appels vers le backend FastAPI.
 * Pourquoi un service séparé ?
 * - Point unique de configuration (baseURL, headers)
 * - Facile à modifier si l'API change
 * - Réutilisable depuis tous les composants
 */

import axios from 'axios';

const api = axios.create({
  baseURL: 'https://streamgrab-video-downloader.onrender.com/api/v1',
  timeout: 90000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Intercepteur pour ajouter le token JWT à chaque requête
 */
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ============ AUTHENTIFICATION ============

/**
 * Enregistre un nouvel utilisateur
 * @param {string} username - Nom d'utilisateur
 * @param {string} email - Email de l'utilisateur
 * @param {string} password - Mot de passe (minimum 8 caractères)
 * @returns {Promise<{access_token: string, token_type: string, user: object}>}
 */
export async function register(username, email, password) {
  const response = await api.post('/auth/register', { username, email, password });
  if (response.data.access_token) {
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('user', JSON.stringify(response.data.user));
  }
  return response.data;
}

/**
 * Se connecte avec un utilisateur
 * @param {string} username - Nom d'utilisateur
 * @param {string} password - Mot de passe
 * @returns {Promise<{access_token: string, token_type: string, user: object}>}
 */
export async function login(username, password) {
  const response = await api.post('/auth/login', { username, password });
  if (response.data.access_token) {
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('user', JSON.stringify(response.data.user));
  }
  return response.data;
}

/**
 * Se déconnecte (supprime le token local)
 */
export function logout() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
}

/**
 * Obtient les informations de l'utilisateur actuel
 */
export function getCurrentUser() {
  const userStr = localStorage.getItem('user');
  return userStr ? JSON.parse(userStr) : null;
}

/**
 * Vérifie si l'utilisateur est connecté
 */
export function isAuthenticated() {
  return !!localStorage.getItem('access_token');
}

// ============ VIDÉOS ============

/**
 * Analyse une vidéo à partir de son URL
 * @param {string} url - URL de la vidéo
 * @returns {Promise<object>} Métadonnées de la vidéo
 */
export async function getVideoInfo(url) {
  const response = await api.post('/video/info', { url });
  return response.data;
}

/**
 * Lance un téléchargement asynchrone et retourne un task_id
 * @param {string} url - URL de la vidéo
 * @param {string} format - 'mp4' ou 'mp3'
 * @returns {Promise<{task_id: string, status: string}>}
 */
export async function startAsyncDownload(url, format) {
  const response = await api.post('/video/download/async', { url, format });
  return response.data;
}

/**
 * Récupère la progression d'un téléchargement asynchrone
 * @param {string} taskId - Identifiant de la tâche
 * @returns {Promise<{task_id: string, status: string, progress: number, speed?: string, eta?: number, filename?: string, error?: string}>}
 */
export async function getDownloadProgress(taskId) {
  const response = await api.get(`/video/download/async/${taskId}/progress`);
  return response.data;
}

/**
 * Récupère l'URL de téléchargement du fichier final
 * @param {string} taskId - Identifiant de la tâche
 * @returns {string} URL pour télécharger le fichier
 */
export function getDownloadFileUrl(taskId) {
  return `/api/v1/video/download/async/${taskId}/file`;
}

/**
 * Télécharge une vidéo dans le format demandé (synchrone, sans barre de progression)
 * @param {string} url - URL de la vidéo
 * @param {string} format - 'mp4' ou 'mp3'
 * @returns {Promise<Blob>} Fichier téléchargé
 */
export async function downloadVideo(url, format) {
  const response = await api.post('/video/download', { url, format }, {
    responseType: 'blob',
    timeout: 600000, // 10 minutes pour le téléchargement
  });
  return response;
}

/**
 * Vérifie que l'API est opérationnelle
 */
/**
 * Connecte un utilisateur via OAuth (Google / Facebook)
 * @param {string} provider - 'google' ou 'facebook'
 * @param {string} token - Token ID du fournisseur OAuth
 * @returns {Promise<{access_token: string, token_type: string, user: object}>}
 */
export async function socialLogin(provider, token) {
  const response = await api.post('/auth/social', { provider, token });
  if (response.data.access_token) {
    localStorage.setItem('access_token', response.data.access_token);
    localStorage.setItem('user', JSON.stringify(response.data.user));
  }
  return response.data;
}

export async function healthCheck() {
  const response = await api.get('/health');
  return response.data;
}

export default api;
