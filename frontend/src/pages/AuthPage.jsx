import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Wallet, ArrowRight, ShieldCheck, PieChart, Layers } from 'lucide-react';

export const AuthPage = () => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (isRegister) {
        await register(email, password, fullName, currency);
      } else {
        await login(email, password);
      }
    } catch (err) {
      const msg = err.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Authentication failed. Please verify your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(circle at top, #1e1b4b 0%, #0f172a 100%)',
      padding: '1.5rem',
      fontFamily: 'Inter, system-ui, -apple-system, sans-serif'
    }}>
      <div style={{
        width: '100%',
        maxWidth: '440px',
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '20px',
        padding: '2rem',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6)'
      }}>
        {/* Brand Icon & Heading */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '56px',
            height: '56px',
            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
            borderRadius: '14px',
            marginBottom: '1rem',
            boxShadow: '0 10px 15px -3px rgba(99, 102, 241, 0.4)'
          }}>
            <Wallet size={28} color="#ffffff" />
          </div>
          <h2 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 700, color: '#f8fafc' }}>
            {isRegister ? 'Create an Account' : 'Welcome Back'}
          </h2>
          <p style={{ margin: '6px 0 0', fontSize: '0.875rem', color: '#94a3b8' }}>
            {isRegister
              ? 'Start tracking personal expenses and shared debts'
              : 'Sign in to access your financial dashboard'}
          </p>
        </div>

        {error && (
          <div style={{
            background: '#ef444420',
            border: '1px solid #ef4444',
            color: '#fca5a5',
            borderRadius: '8px',
            padding: '0.75rem',
            marginBottom: '1.25rem',
            fontSize: '0.85rem'
          }}>
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          {isRegister && (
            <>
              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Jane Doe"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  style={{
                    width: '100%',
                    boxSizing: 'border-box',
                    background: '#0f172a',
                    border: '1px solid #334155',
                    color: '#f8fafc',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    fontSize: '0.95rem',
                    outline: 'none'
                  }}
                />
              </div>

              <div style={{ marginBottom: '1rem' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
                  Preferred Currency
                </label>
                <select
                  value={currency}
                  onChange={(e) => setCurrency(e.target.value)}
                  style={{
                    width: '100%',
                    background: '#0f172a',
                    border: '1px solid #334155',
                    color: '#f8fafc',
                    padding: '10px 12px',
                    borderRadius: '8px',
                    fontSize: '0.9rem',
                    outline: 'none'
                  }}
                >
                  <option value="USD">USD ($)</option>
                  <option value="EUR">EUR (€)</option>
                  <option value="GBP">GBP (£)</option>
                  <option value="INR">INR (₹)</option>
                  <option value="CAD">CAD ($)</option>
                </select>
              </div>
            </>
          )}

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
              Email Address
            </label>
            <input
              type="email"
              required
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                background: '#0f172a',
                border: '1px solid #334155',
                color: '#f8fafc',
                padding: '10px 12px',
                borderRadius: '8px',
                fontSize: '0.95rem',
                outline: 'none'
              }}
            />
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
              Password
            </label>
            <input
              type="password"
              required
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                background: '#0f172a',
                border: '1px solid #334155',
                color: '#f8fafc',
                padding: '10px 12px',
                borderRadius: '8px',
                fontSize: '0.95rem',
                outline: 'none'
              }}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              background: '#6366f1',
              color: '#ffffff',
              border: 'none',
              padding: '12px',
              borderRadius: '8px',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '8px',
              transition: 'background 0.2s',
              boxShadow: '0 4px 6px -1px rgba(99, 102, 241, 0.4)'
            }}
          >
            <span>{loading ? 'Processing...' : isRegister ? 'Register' : 'Sign In'}</span>
            <ArrowRight size={18} />
          </button>
        </form>

        <div style={{
          textAlign: 'center',
          marginTop: '1.5rem',
          paddingTop: '1.25rem',
          borderTop: '1px solid #334155',
          fontSize: '0.875rem',
          color: '#94a3b8'
        }}>
          {isRegister ? 'Already have an account?' : "Don't have an account yet?"}{' '}
          <button
            type="button"
            onClick={() => {
              setIsRegister(!isRegister);
              setError(null);
            }}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#818cf8',
              fontWeight: 600,
              cursor: 'pointer',
              textDecoration: 'underline'
            }}
          >
            {isRegister ? 'Sign In' : 'Register'}
          </button>
        </div>
      </div>
    </div>
  );
};

