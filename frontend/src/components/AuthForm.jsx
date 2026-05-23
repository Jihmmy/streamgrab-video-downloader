import React, { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { login, register, socialLogin } from '../services/api';
import { FacebookLoginButton } from './FacebookLogin';

export default function AuthForm() {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isLogin) {
        const response = await login(formData.username, formData.password);
        console.log('Login réussi:', response.user);
        alert(`Bienvenue ${response.user.username}!`);
        window.location.reload();
      } else {
        const response = await register(formData.username, formData.email, formData.password);
        console.log('Inscription réussie:', response.user);
        alert(`Compte créé! Bienvenue ${response.user.username}`);
        window.location.reload();
      }
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Erreur d\'authentification');
      console.error('Erreur:', err);
    } finally {
      setLoading(false);
    }
  };

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      setError(null);
      const data = await socialLogin('google', credentialResponse.credential);
      console.log('Connexion Google réussie:', data.user);
      alert(`Bienvenue ${data.user.username}!`);
      window.location.reload();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Erreur de connexion Google');
    }
  };

  const handleFacebookSuccess = async (response) => {
    try {
      setError(null);
      const data = await socialLogin('facebook', response.accessToken);
      console.log('Connexion Facebook réussie:', data.user);
      alert(`Bienvenue ${data.user.username}!`);
      window.location.reload();
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Erreur de connexion Facebook');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-2xl p-8 w-full max-w-md">
        <h1 className="text-3xl font-bold text-center mb-8 text-gray-800">
          {isLogin ? 'Se connecter' : 'S\'inscrire'}
        </h1>

        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Username */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Nom d'utilisateur
            </label>
            <input
              type="text"
              name="username"
              value={formData.username}
              onChange={handleChange}
              required
              minLength="3"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              placeholder="john_doe"
            />
          </div>

          {/* Email - only for register */}
          {!isLogin && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
                placeholder="john@example.com"
              />
            </div>
          )}

          {/* Password */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Mot de passe
            </label>
            <input
              type="password"
              name="password"
              value={formData.password}
              onChange={handleChange}
              required
              minLength={isLogin ? "1" : "8"}
              maxLength="72"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition"
              placeholder={isLogin ? "Votre mot de passe" : "Minimum 8 caractères"}
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-600 text-white font-bold py-2 px-4 rounded-lg hover:shadow-lg transition transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Chargement...' : isLogin ? 'Se connecter' : 'S\'inscrire'}
          </button>
        </form>

        {/* Séparateur */}
        <div className="flex items-center my-6">
          <div className="flex-1 border-t border-gray-300"></div>
          <span className="px-4 text-sm text-gray-500">ou</span>
          <div className="flex-1 border-t border-gray-300"></div>
        </div>

        {/* Boutons sociaux */}
        <div className="space-y-3">
          {/* Google */}
          <div className="flex justify-center">
            {googleClientId ? (
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={() => setError('Échec de la connexion Google')}
                size="large"
                width="300"
                theme="outline"
                text={isLogin ? "signin_with" : "signup_with"}
              />
            ) : (
              <a
                href="https://console.cloud.google.com/apis/credentials"
                target="_blank"
                rel="noopener noreferrer"
                className="w-full flex items-center justify-center gap-3 px-4 py-2.5 border border-gray-300 text-gray-500 font-medium rounded-lg hover:bg-gray-50 transition text-sm"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                Configurer Google Login
              </a>
            )}
          </div>

          {/* Facebook */}
          <FacebookLoginButton onSuccess={handleFacebookSuccess} />
        </div>

        {/* Toggle Login/Register */}
        <div className="mt-6 text-center">
          <p className="text-gray-600 text-sm">
            {isLogin ? "Pas de compte?" : "Déjà inscrit?"}
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin);
                setError(null);
                setFormData({ username: '', email: '', password: '' });
              }}
              className="ml-2 text-blue-600 font-semibold hover:text-blue-800 transition"
            >
              {isLogin ? 'S\'inscrire' : 'Se connecter'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}