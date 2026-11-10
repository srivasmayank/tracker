import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Wallet, LogOut, User as UserIcon, Users, UserCheck, Repeat } from 'lucide-react';

export const Navbar = ({ currentTab, onTabChange }) => {
  const { user, logout } = useAuth();

  return (
    <header style={{
      background: '#1e293b',
      borderBottom: '1px solid #334155',
      color: '#f8fafc',
      padding: '0.75rem 1.5rem',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      position: 'sticky',
      top: 0,
      zIndex: 40,
      flexWrap: 'wrap',
      gap: '1rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
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
              background: '#065f46',
              color: '#6ee7b7',
              padding: '2px 6px',
              borderRadius: '4px',
              textTransform: 'uppercase',
              fontWeight: '600'
            }}>
              Phase 5: Background Jobs
            </span>
          </div>
        </div>

        {/* Navigation Tabs */}
        {user && (
          <nav style={{ display: 'flex', gap: '0.5rem', background: '#0f172a', padding: '4px', borderRadius: '10px', border: '1px solid #334155' }}>
            <button
              onClick={() => onTabChange('personal')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 14px',
                borderRadius: '8px',
                border: 'none',
                background: currentTab === 'personal' ? '#6366f1' : 'transparent',
                color: currentTab === 'personal' ? '#ffffff' : '#94a3b8',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <UserCheck size={16} />
              Personal
            </button>
            <button
              onClick={() => onTabChange('groups')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 14px',
                borderRadius: '8px',
                border: 'none',
                background: currentTab === 'groups' ? '#6366f1' : 'transparent',
                color: currentTab === 'groups' ? '#ffffff' : '#94a3b8',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <Users size={16} />
              Splitwise Groups
            </button>
            <button
              onClick={() => onTabChange('recurring')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '6px 14px',
                borderRadius: '8px',
                border: 'none',
                background: currentTab === 'recurring' ? '#6366f1' : 'transparent',
                color: currentTab === 'recurring' ? '#ffffff' : '#94a3b8',
                fontWeight: 600,
                fontSize: '0.85rem',
                cursor: 'pointer',
                transition: 'all 0.2s'
              }}
            >
              <Repeat size={16} />
              Subscriptions
            </button>
          </nav>
        )}
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
              fontWeight: '500'
            }}
          >
            <LogOut size={15} />
            Logout
          </button>
        </div>
      )}
    </header>
  );
};
