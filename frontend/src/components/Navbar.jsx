import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Wallet, LogOut, User as UserIcon } from 'lucide-react';

export const Navbar = () => {
  const { user, logout } = useAuth();

  return (
    <header style={{
      background: '#1e293b',
      borderBottom: '1px solid #334155',
      color: '#f8fafc',
      padding: '0.85rem 1.5rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 40
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{
          background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
          borderRadius: '10px',
          padding: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 6px -1px rgba(99, 102, 241, 0.4)'
        }}>
          <Wallet size={22} color="#ffffff" />
        </div>
        <div>
          <span style={{ fontSize: '1.2rem', fontWeight: '700', letterSpacing: '-0.025em' }}>
            Tracer<span style={{ color: '#818cf8' }}>Expense</span>
          </span>
          <span style={{
            fontSize: '0.65rem',
            marginLeft: '8px',
            background: '#312e81',
            color: '#c7d2fe',
            padding: '2px 6px',
            borderRadius: '4px',
            textTransform: 'uppercase',
            fontWeight: '600'
          }}>
            Phase 1
          </span>
        </div>
      </div>

      {user && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: '#0f172a',
            padding: '6px 12px',
            borderRadius: '8px',
            border: '1px solid #334155',
            fontSize: '0.875rem'
          }}>
            <UserIcon size={16} color="#94a3b8" />
            <span style={{ fontWeight: '500' }}>{user.full_name}</span>
            <span style={{
              background: '#334155',
              color: '#38bdf8',
              fontSize: '0.75rem',
              padding: '2px 6px',
              borderRadius: '4px',
              fontWeight: '600'
            }}>
              {user.currency || 'USD'}
            </span>
          </div>

          <button
            onClick={logout}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'transparent',
              color: '#f87171',
              border: '1px solid #ef444440',
              padding: '6px 12px',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '0.85rem',
              fontWeight: '500',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => (e.currentTarget.style.background = '#ef444420')}
            onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
          >
            <LogOut size={15} />
            Logout
          </button>
        </div>
      )}
    </header>
  );
};

