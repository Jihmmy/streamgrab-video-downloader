import React, { useState, useRef, useEffect } from 'react';
import { getVideoInfo, startAsyncDownload, getDownloadProgress, getDownloadFileUrl, isAuthenticated } from './services/api.js';
import ProgressBar from './components/ProgressBar.jsx';
import AuthForm from './components/AuthForm.jsx';
import UserProfile from './components/UserProfile.jsx';

// Icônes SVG inline (pas de dépendance externe)
const IconVideo = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
  </svg>
);

const IconAudio = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
  </svg>
);

const IconDownload = () => (
  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
  </svg>
);

function App() {
  const [url, setUrl] = useState('');
  const [videoInfo, setVideoInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState(null);

  // État du téléchargement asynchrone
  const [downloadTask, setDownloadTask] = useState(null); // { task_id, status, progress, speed, eta, error, filename }
  const progressInterval = useRef(null);

  // Nettoyage de l'intervalle de polling au démontage
  useEffect(() => {
    return () => {
      if (progressInterval.current) {
        clearInterval(progressInterval.current);
      }
    };
  }, []);

  // Polling de la progression
  const startProgressPolling = (taskId) => {
    // Nettoyer l'ancien intervalle si existant
    if (progressInterval.current) {
      clearInterval(progressInterval.current);
    }

    progressInterval.current = setInterval(async () => {
      try {
        const progress = await getDownloadProgress(taskId);
        setDownloadTask(progress);

        // Téléchargement terminé → déclencher le fichier
        if (progress.status === 'completed') {
          clearInterval(progressInterval.current);
          progressInterval.current = null;

          // Déclencher le téléchargement du fichier
          const fileUrl = getDownloadFileUrl(taskId);
          const a = document.createElement('a');
          a.href = fileUrl;
          a.download = progress.filename || `streamgrab.${progress.format}`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);

          // Attendre 2s puis réinitialiser l'état de téléchargement
          setTimeout(() => {
            setDownloading(false);
          }, 3000);
        }

        // Erreur
        if (progress.status === 'error') {
          clearInterval(progressInterval.current);
          progressInterval.current = null;
          setError(progress.error || 'Erreur lors du téléchargement');
          setDownloading(false);
        }
      } catch (err) {
        // Erreur de polling (ex: tâche expirée) → arrêter
        clearInterval(progressInterval.current);
        progressInterval.current = null;
        setDownloading(false);
        setError('Erreur de suivi du téléchargement');
      }
    }, 1000); // Polling toutes les 1 secondes
  };

  // Analyse de la vidéo
  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;

    setLoading(true);
    setError(null);
    setVideoInfo(null);
    setDownloadTask(null);

    try {
      const info = await getVideoInfo(url.trim());
      setVideoInfo(info);
    } catch (err) {
      const message = err.response?.data?.detail?.error 
        || err.response?.data?.error 
        || err.message 
        || 'Erreur lors de l\'analyse';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  // Téléchargement asynchrone avec barre de progression
  const handleDownload = async (format) => {
    if (!videoInfo) return;

    setDownloading(true);
    setError(null);
    setDownloadTask(null);

    try {
      // 1. Lancer le téléchargement asynchrone
      const { task_id } = await startAsyncDownload(videoInfo.webpage_url, format);
      
      // 2. Initialiser l'état de progression
      setDownloadTask({
        task_id,
        status: 'pending',
        progress: 0,
        format,
      });

      // 3. Démarrer le polling de la progression
      startProgressPolling(task_id);
    } catch (err) {
      const message = err.response?.data?.detail?.error 
        || err.response?.data?.error 
        || err.message 
        || 'Erreur lors du lancement du téléchargement';
      setError(message);
      setDownloading(false);
    }
  };

  // Formatage de la durée
  const formatDuration = (seconds) => {
    if (!seconds) return '';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    if (h > 0) return `${h}h ${m}m ${s}s`;
    return `${m}m ${s}s`;
  };

  // Vérifier l'authentification
  if (!isAuthenticated()) {
    return <AuthForm />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-purple-950">
      {/* Header */}
      <header className="border-b border-gray-800">
        <div className="max-w-5xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">StreamGrab</h1>
                <p className="text-sm text-gray-400">Téléchargement vidéo simplifié</p>
              </div>
            </div>
            <UserProfile />
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Formulaire URL */}
        <section className="mb-8">
          <form onSubmit={handleAnalyze} className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 backdrop-blur-sm">
            <label className="block text-sm font-medium text-gray-300 mb-2">
              URL de la vidéo
            </label>
            <div className="flex gap-3">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                className="flex-1 bg-gray-800 border border-gray-700 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                disabled={loading || downloading}
              />
              <button
                type="submit"
                disabled={loading || downloading || !url.trim()}
                className="px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-medium rounded-xl hover:from-purple-500 hover:to-pink-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-purple-900/30"
              >
                {loading ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Analyse...
                  </span>
                ) : 'Analyser'}
              </button>
            </div>
          </form>
        </section>

        {/* Messages d'erreur */}
        {error && (
          <div className="mb-8 p-4 bg-red-900/30 border border-red-800 rounded-xl text-red-400 text-sm">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Résultat de l'analyse */}
        {videoInfo && (
          <section className="space-y-6">
            {/* Carte vidéo */}
            <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 backdrop-blur-sm">
              <div className="flex flex-col md:flex-row gap-6">
                {/* Miniature */}
                {videoInfo.thumbnail && (
                  <div className="flex-shrink-0">
                    <img
                      src={videoInfo.thumbnail}
                      alt={videoInfo.title}
                      className="w-full md:w-64 h-40 object-cover rounded-xl"
                      onError={(e) => { e.target.style.display = 'none' }}
                    />
                  </div>
                )}
                
                {/* Infos */}
                <div className="flex-1 min-w-0">
                  <h2 className="text-xl font-bold text-white mb-2 truncate">
                    {videoInfo.title}
                  </h2>
                  
                  <div className="flex flex-wrap gap-4 mb-4">
                    {videoInfo.duration && (
                      <span className="flex items-center gap-1 text-sm text-gray-400">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        {formatDuration(videoInfo.duration)}
                      </span>
                    )}
                    {videoInfo.uploader && (
                      <span className="flex items-center gap-1 text-sm text-gray-400">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        {videoInfo.uploader}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Formats disponibles */}
            <div className="bg-gray-900/50 border border-gray-800 rounded-2xl p-6 backdrop-blur-sm">
              <h3 className="text-lg font-semibold text-white mb-4">
                Formats disponibles
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Bouton MP4 */}
                <button
                  onClick={() => handleDownload('mp4')}
                  disabled={downloading || !videoInfo.available_formats?.includes('mp4')}
                  className={`p-5 rounded-xl border transition-all text-left ${
                    videoInfo.available_formats?.includes('mp4')
                      ? 'bg-blue-900/20 border-blue-800 hover:bg-blue-900/40 hover:border-blue-600 cursor-pointer'
                      : 'bg-gray-800/50 border-gray-700 opacity-50 cursor-not-allowed'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 bg-blue-600/20 rounded-lg flex items-center justify-center">
                        <IconVideo />
                      </div>
                      <div>
                        <div className="text-white font-medium">MP4</div>
                        <div className="text-xs text-gray-400">Vidéo + Audio</div>
                      </div>
                    </div>
                    {downloading && downloadTask?.format === 'mp4' ? (
                      <svg className="animate-spin h-5 w-5 text-blue-400" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                    ) : (
                      <IconDownload />
                    )}
                  </div>
                </button>

                {/* Bouton MP3 */}
                <button
                  onClick={() => handleDownload('mp3')}
                  disabled={downloading || !videoInfo.available_formats?.includes('mp3')}
                  className={`p-5 rounded-xl border transition-all text-left ${
                    videoInfo.available_formats?.includes('mp3')
                      ? 'bg-green-900/20 border-green-800 hover:bg-green-900/40 hover:border-green-600 cursor-pointer'
                      : 'bg-gray-800/50 border-gray-700 opacity-50 cursor-not-allowed'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className="w-10 h-10 bg-green-600/20 rounded-lg flex items-center justify-center">
                        <IconAudio />
                      </div>
                      <div>
                        <div className="text-white font-medium">MP3</div>
                        <div className="text-xs text-gray-400">Audio uniquement</div>
                      </div>
                    </div>
                    {downloading && downloadTask?.format === 'mp3' ? (
                      <svg className="animate-spin h-5 w-5 text-green-400" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                    ) : (
                      <IconDownload />
                    )}
                  </div>
                  {videoInfo.available_formats?.includes('mp3') ? (
                    <p className="text-xs text-gray-400 mt-1">
                      Meilleure qualité audio disponible
                    </p>
                  ) : (
                    <p className="text-xs text-gray-500 mt-1">
                      Non disponible pour cette vidéo
                    </p>
                  )}
                </button>
              </div>

              {/* Barre de progression du téléchargement */}
              {downloading && downloadTask && (
                <div className="mt-4">
                  <ProgressBar
                    progress={downloadTask.progress}
                    status={downloadTask.status}
                    speed={downloadTask.speed}
                    eta={downloadTask.eta}
                    error={downloadTask.error}
                  />
                </div>
              )}
            </div>

            {/* Formats détaillés */}
            {videoInfo.formats && videoInfo.formats.length > 0 && (
              <details className="bg-gray-900/50 border border-gray-800 rounded-2xl backdrop-blur-sm">
                <summary className="px-6 py-4 cursor-pointer text-gray-400 hover:text-gray-300 font-medium transition-colors">
                  Tous les formats disponibles ({videoInfo.formats.length})
                </summary>
                <div className="px-6 pb-4 max-h-80 overflow-y-auto">
                  <div className="grid grid-cols-1 gap-2">
                    {videoInfo.formats.map((fmt, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-gray-800/50 rounded-lg text-sm">
                        <div className="flex items-center gap-3">
                          <span className="text-gray-400 font-mono text-xs">{fmt.ext}</span>
                          <span className="text-white">{fmt.quality || 'N/A'}</span>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-gray-500">
                          {fmt.filesize_mb && <span>{fmt.filesize_mb} Mo</span>}
                          {fmt.has_video && <span className="text-blue-400">🎬</span>}
                          {fmt.has_audio && <span className="text-green-400">🎵</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </details>
            )}
          </section>
        )}
      </main>
    </div>
  );
}

export default App;