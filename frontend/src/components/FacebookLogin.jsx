import React, { useState } from 'react';

/**
 * Bouton "Se connecter avec Facebook" personnalisé.
 * 
 * Utilise le SDK Facebook chargé via le script externe (FB.init).
 * Pour utiliser Facebook Login, ajoute ces variables d'environnement :
 *   VITE_FACEBOOK_APP_ID=<ton_app_id>
 * 
 * Le script SDK Facebook est chargé automatiquement au premier clic.
 */
export function FacebookLoginButton({ onSuccess, onError }) {
  const [loading, setLoading] = useState(false);

  const handleClick = () => {
    setLoading(true);

    // Vérifier si le SDK Facebook est déjà chargé
    if (window.FB) {
      loginWithFacebook();
      return;
    }

    // Charger le SDK Facebook dynamiquement
    const appId = import.meta.env.VITE_FACEBOOK_APP_ID;

    if (!appId) {
      setLoading(false);
      if (onError) {
        onError({ message: 'Facebook App ID non configuré (VITE_FACEBOOK_APP_ID)' });
      } else {
        alert(
          'Facebook Login n\'est pas configuré.\n\n' +
          'Si tu es développeur et veux le tester en local sans clé Facebook,\n' +
          'utilise la console navigateur avec :\n' +
          '  localStorage.setItem("fb_test_token", JSON.stringify({\n' +
          '    accessToken: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InRlc3RAZmFjZWJvb2suY29tIiwibmFtZSI6IlRlc3QgVXNlciJ9.test",\n' +
          '  }))\n' +
          'puis rafraîchis la page.'
        );
      }
      return;
    }

    // Charger le script SDK
    const script = document.createElement('script');
    script.src = 'https://connect.facebook.net/fr_FR/sdk.js';
    script.onload = () => {
      window.FB.init({
        appId,
        version: 'v18.0',
        cookie: true,
        xfbml: false,
      });
      loginWithFacebook();
    };
    script.onerror = () => {
      setLoading(false);
      if (onError) onError({ message: 'Impossible de charger le SDK Facebook' });
    };
    document.body.appendChild(script);
  };

  const loginWithFacebook = () => {
    window.FB.login(
      (response) => {
        setLoading(false);
        if (response.authResponse) {
          if (onSuccess) onSuccess({ accessToken: response.authResponse.accessToken });
        } else {
          if (onError) onError({ message: 'Connexion Facebook annulée' });
        }
      },
      { scope: 'email,public_profile' }
    );
  };

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={loading}
      className="w-full flex items-center justify-center gap-3 px-4 py-2.5 bg-[#1877F2] text-white font-medium rounded-lg hover:bg-[#166fe5] transition transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
    >
      {loading ? (
        <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      ) : (
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
        </svg>
      )}
      {loading ? 'Connexion...' : 'Se connecter avec Facebook'}
    </button>
  );
}

export default FacebookLoginButton;