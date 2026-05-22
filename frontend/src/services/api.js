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
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

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
export async function healthCheck() {
  const response = await api.get('/health');
  return response.data;
}

export default api;