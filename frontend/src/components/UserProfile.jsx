import React from 'react';
import { logout, getCurrentUser } from '../services/api';

export default function UserProfile() {
  const user = getCurrentUser();

  const handleLogout = () => {
    logout();
    alert('Déconnecté!');
    window.location.reload();
  };

  if (!user) {
    return null;
  }

  return (
    <div className="flex items-center gap-4 bg-white rounded-lg p-4 shadow-md">
      <div className="flex-1">
        <p className="text-sm font-semibold text-gray-700">
          👤 {user.username}
        </p>
        <p className="text-xs text-gray-500">
          {user.email}
        </p>
      </div>
      <button
        onClick={handleLogout}
        className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition font-medium text-sm"
      >
        Déconnexion
      </button>
    </div>
  );
}
