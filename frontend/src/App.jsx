import React from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AuthPage } from './pages/AuthPage';
import { Dashboard } from './pages/Dashboard';

const AppContent = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#0f172a',
        color: '#94a3b8',
        fontSize: '1rem',
        fontFamily: 'Inter, system-ui, sans-serif'
      }}>
        Loading session...
      </div>
    );
  }

  return user ? <Dashboard /> : <AuthPage />;
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;

