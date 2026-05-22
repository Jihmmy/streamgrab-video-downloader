import React, { useEffect, useState } from 'react';

/**
 * Barre de progression animée avec design glassmorphisme pour le téléchargement.
 * 
 * Utilisation :
 * <ProgressBar 
 *   progress={45}        // Pourcentage 0-100
 *   status="downloading" // pending | downloading | processing | completed | error
 *   speed="2.5 MiB/s"    // Vitesse de téléchargement
 *   eta={120}            // Temps restant en secondes
 *   total_bytes={...}    // Taille totale en octets (optionnel)
 *   downloaded_bytes={...} // Téléchargé en octets (optionnel)
 *   error="Message"      // Message d'erreur si status=error
 *   variant="inline"     // "inline" | "overlay" - style d'affichage
 * />
 */
function ProgressBar({ progress, status, speed, eta, error, total_bytes, downloaded_bytes, variant = 'inline' }) {
  const [displayProgress, setDisplayProgress] = useState(0);
  const [showCheckmark, setShowCheckmark] = useState(false);

  // Animation smooth du pourcentage
  useEffect(() => {
    const timer = setTimeout(() => {
      setDisplayProgress(progress);
    }, 50);
    return () => clearTimeout(timer);
  }, [progress]);

  // Animation checkmark quand completed
  useEffect(() => {
    if (status === 'completed') {
      const timer = setTimeout(() => setShowCheckmark(true), 300);
      return () => clearTimeout(timer);
    } else {
      setShowCheckmark(false);
    }
  }, [status]);

  // Formater les bytes en taille lisible
  const formatBytes = (bytes) => {
    if (!bytes || bytes <= 0) return null;
    const units = ['o', 'Ko', 'Mo', 'Go', 'To'];
    let value = bytes;
    let unitIndex = 0;
    while (value >= 1024 && unitIndex < units.length - 1) {
      value /= 1024;
      unitIndex++;
    }
    return `${value.toFixed(unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
  };

  // Formater le temps restant
  const formatETA = (seconds) => {
    if (!seconds || seconds <= 0) return null;
    if (seconds < 60) return `${seconds}s`;
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    if (m < 60) return `${m}m ${s}s`;
    const h = Math.floor(m / 60);
    const remainingM = m % 60;
    return `${h}h ${remainingM}m`;
  };

  // Configuration par statut
  const getStatusConfig = () => {
    switch (status) {
      case 'pending':
        return {
          gradient: 'from-blue-500/20 to-purple-500/20',
          border: 'border-blue-500/30',
          barGradient: 'from-blue-500 via-purple-500 to-pink-500',
          textColor: 'text-blue-300',
          accentColor: 'bg-blue-500',
          icon: (
            <svg className="w-5 h-5 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
          label: 'En attente...',
          bgPattern: 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-blue-900/10 via-gray-900/50 to-gray-900/50',
        };
      case 'downloading':
        return {
          gradient: 'from-green-500/20 to-emerald-500/20',
          border: 'border-green-500/30',
          barGradient: 'from-green-400 via-emerald-500 to-teal-500',
          textColor: 'text-green-300',
          accentColor: 'bg-green-500',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          ),
          label: 'Téléchargement en cours...',
          bgPattern: 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-green-900/10 via-gray-900/50 to-gray-900/50',
        };
      case 'processing':
        return {
          gradient: 'from-yellow-500/20 to-orange-500/20',
          border: 'border-yellow-500/30',
          barGradient: 'from-yellow-400 via-orange-500 to-rose-500',
          textColor: 'text-yellow-300',
          accentColor: 'bg-yellow-500',
          icon: (
            <svg className="w-5 h-5 animate-spin" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ),
          label: 'Conversion en cours...',
          bgPattern: 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-yellow-900/10 via-gray-900/50 to-gray-900/50',
        };
      case 'completed':
        return {
          gradient: 'from-green-500/20 to-emerald-500/20',
          border: 'border-green-500/40',
          barGradient: 'from-green-400 to-green-500',
          textColor: 'text-green-300',
          accentColor: 'bg-green-500',
          icon: (
            <div className="relative">
              <svg className={`w-6 h-6 transition-all duration-500 ${showCheckmark ? 'scale-100 opacity-100' : 'scale-0 opacity-0'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {!showCheckmark && (
                <svg className="w-5 h-5 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              )}
            </div>
          ),
          label: 'Téléchargement terminé !',
          bgPattern: 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-green-900/10 via-gray-900/50 to-gray-900/50',
        };
      case 'error':
        return {
          gradient: 'from-red-500/20 to-rose-500/20',
          border: 'border-red-500/30',
          barGradient: 'from-red-500 to-rose-600',
          textColor: 'text-red-300',
          accentColor: 'bg-red-500',
          icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
          label: error || 'Erreur lors du téléchargement',
          bgPattern: 'bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-red-900/10 via-gray-900/50 to-gray-900/50',
        };
      default:
        return {
          gradient: 'from-gray-500/20 to-gray-600/20',
          border: 'border-gray-500/30',
          barGradient: 'from-gray-400 to-gray-500',
          textColor: 'text-gray-400',
          accentColor: 'bg-gray-500',
          icon: null,
          label: '',
          bgPattern: '',
        };
    }
  };

  const config = getStatusConfig();
  const pct = Math.min(100, Math.max(0, Math.round(displayProgress)));
  const isActive = status === 'downloading' || status === 'processing';
  const isFinished = status === 'completed' || status === 'error';
  const fileSize = total_bytes ? formatBytes(total_bytes) : null;
  const downloadedSize = downloaded_bytes ? formatBytes(downloaded_bytes) : null;

  // Classes de base selon le variant
  const containerClasses = variant === 'overlay'
    ? `fixed bottom-6 left-4 right-4 max-w-lg mx-auto z-50 transition-all duration-500 ${isFinished ? 'translate-y-0 opacity-100' : 'translate-y-0 opacity-100'}`
    : `transition-all duration-500`;

  // Overlay backdrop pour l'overlay
  const backdrop = variant === 'overlay' && status !== 'completed' && status !== 'error' ? (
    <div className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40" />
  ) : null;

  return (
    <>
      {backdrop}
      <div className={`${containerClasses} ${config.bgPattern} ${config.gradient} ${config.border} border rounded-2xl p-5 backdrop-blur-xl shadow-2xl shadow-black/30`}>
        {/* En-tête avec icône, statut et pourcentage */}
        <div className="flex items-center gap-3 mb-3">
          <div className={`flex-shrink-0 ${config.textColor} transition-transform duration-300 ${status === 'completed' && showCheckmark ? 'scale-110' : 'scale-100'}`}>
            {config.icon}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between">
              <span className={`text-sm font-medium ${config.textColor} truncate`}>
                {config.label}
              </span>
              <span className={`text-sm font-bold tabular-nums ml-2 ${config.textColor} ${isActive ? 'animate-pulse' : ''}`}>
                {isActive || status === 'pending' ? `${pct}%` : ''}
                {status === 'completed' && <span className="text-green-400">100%</span>}
              </span>
            </div>
          </div>
        </div>

        {/* Barre de progression */}
        {status !== 'error' && (
          <div className="relative h-3 bg-gray-800/60 rounded-full overflow-hidden ring-1 ring-white/5">
            {/* Barre de fond avec motif */}
            <div
              className={`absolute left-0 top-0 h-full rounded-full transition-all duration-700 ease-out bg-gradient-to-r ${config.barGradient}`}
              style={{ width: `${status === 'completed' ? 100 : pct}%` }}
            >
              {/* Effet de brillance (shimmer) */}
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" 
                   style={{ backgroundSize: '200% 100%' }} />
              {/* Lueur au bout de la barre */}
              <div className={`absolute right-0 top-1/2 -translate-y-1/2 w-6 h-6 ${config.accentColor} rounded-full blur-xl opacity-40`} />
            </div>
            {/* Points de progression sur la barre (effet visuel) */}
            {isActive && (
              <div className="absolute inset-0 flex items-center justify-between px-1">
                {[...Array(20)].map((_, i) => (
                  <div
                    key={i}
                    className="w-0.5 h-1.5 bg-white/5 rounded-full"
                    style={{ opacity: i < pct / 5 ? 0.15 : 0 }}
                  />
                ))}
              </div>
            )}
          </div>
        )}

        {/* Informations supplémentaires */}
        {(isActive || isFinished) && (
          <div className="mt-3 space-y-2">
            {/* Ligne vitesse, ETA, tailles */}
            <div className="flex items-center flex-wrap gap-x-4 gap-y-1 text-xs">
              {/* Vitesse */}
              {speed && (
                <span className="flex items-center gap-1 text-gray-400">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  {speed}
                </span>
              )}
              {/* ETA */}
              {eta && eta > 0 && (
                <span className="flex items-center gap-1 text-gray-400">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Restant : {formatETA(eta)}
                </span>
              )}
              {/* Tailles */}
              {downloadedSize && fileSize && (
                <span className="flex items-center gap-1 text-gray-400">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7" />
                  </svg>
                  {downloadedSize} / {fileSize}
                </span>
              )}
              {downloadedSize && !fileSize && (
                <span className="flex items-center gap-1 text-gray-400">
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7" />
                  </svg>
                  {downloadedSize}
                </span>
              )}
              {/* Fallback */}
              {!speed && !eta && !downloadedSize && isActive && (
                <span className="text-gray-500 italic">
                  Téléchargement en cours...
                </span>
              )}
            </div>
          </div>
        )}

        {/* Message d'erreur détaillé */}
        {status === 'error' && error && (
          <div className="mt-3 flex items-start gap-2 text-xs text-red-300 bg-red-900/30 border border-red-800/30 rounded-lg p-3">
            <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <span>{error}</span>
          </div>
        )}
      </div>
    </>
  );
}

export default ProgressBar;