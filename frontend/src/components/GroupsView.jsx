import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api/client';
import { CreateGroupModal } from './CreateGroupModal';
import { GroupDetailView } from './GroupDetailView';
import { Users, PlusCircle, ArrowRight, ShieldCheck } from 'lucide-react';

export const GroupsView = ({ categories = [] }) => {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedGroupId, setSelectedGroupId] = useState(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const fetchGroups = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/groups');
      setGroups(res.data);
    } catch (err) {
      console.error('Failed to load groups', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchGroups();
  }, [fetchGroups]);

  // If a group is selected, show its detailed ledger
  if (selectedGroupId) {
    return (
      <GroupDetailView
        groupId={selectedGroupId}
        onBack={() => {
          setSelectedGroupId(null);
          fetchGroups();
        }}
        categories={categories}
      />
    );
  }

  return (
    <div>
      {/* Top Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '2rem'
      }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: 0, letterSpacing: '-0.02em', color: '#f8fafc' }}>
            Splitwise Groups
          </h1>
          <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: '0.9rem' }}>
            Collaborate on shared trips, household expenses, and settle debts with greedy graph simplification.
          </p>
        </div>

        <button
          onClick={() => setIsCreateModalOpen(true)}
          style={{
            background: '#6366f1',
            color: '#ffffff',
            border: 'none',
            padding: '10px 18px',
            borderRadius: '8px',
            fontSize: '0.95rem',
            fontWeight: 600,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 4px 6px -1px rgba(99, 102, 241, 0.4)'
          }}
        >
          <PlusCircle size={18} />
          Create Group
        </button>
      </div>

      {/* Groups Grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>
          Loading your groups...
        </div>
      ) : groups.length === 0 ? (
        <div style={{
          background: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '16px',
          padding: '3rem',
          textAlign: 'center'
        }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '64px',
            height: '64px',
            background: '#6366f120',
            borderRadius: '16px',
            marginBottom: '1rem'
          }}>
            <Users size={32} color="#818cf8" />
          </div>
          <h3 style={{ margin: '0 0 8px', fontSize: '1.25rem', color: '#f8fafc' }}>
            No Groups Found
          </h3>
          <p style={{ margin: '0 0 1.5rem', color: '#94a3b8', maxWidth: '400px', marginInline: 'auto', fontSize: '0.9rem' }}>
            Create a group for an apartment, trip, or dinner party to split bills and automatically optimize repayments.
          </p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            style={{
              background: '#6366f1',
              color: '#ffffff',
              border: 'none',
              padding: '10px 20px',
              borderRadius: '8px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Create Your First Group
          </button>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
          gap: '1.25rem'
        }}>
          {groups.map((grp) => (
            <div
              key={grp.id}
              onClick={() => setSelectedGroupId(grp.id)}
              style={{
                background: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '14px',
                padding: '1.5rem',
                cursor: 'pointer',
                transition: 'all 0.2s',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}
              onMouseOver={(e) => {
                e.currentTarget.style.borderColor = '#6366f1';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseOut={(e) => {
                e.currentTarget.style.borderColor = '#334155';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <h3 style={{ margin: 0, fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc' }}>
                    {grp.name}
                  </h3>
                  <span style={{
                    background: '#0f172a',
                    border: '1px solid #334155',
                    color: '#818cf8',
                    fontSize: '0.75rem',
                    padding: '2px 8px',
                    borderRadius: '6px',
                    fontWeight: 600
                  }}>
                    {grp.members.length} {grp.members.length === 1 ? 'member' : 'members'}
                  </span>
                </div>

                <p style={{ margin: '0 0 1.25rem', color: '#94a3b8', fontSize: '0.875rem', minHeight: '38px' }}>
                  {grp.description || 'No description provided.'}
                </p>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingTop: '1rem',
                borderTop: '1px solid #334155',
                fontSize: '0.85rem'
              }}>
                <span style={{ color: '#64748b' }}>
                  Created {new Date(grp.created_at).toLocaleDateString()}
                </span>
                <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#818cf8', fontWeight: 600 }}>
                  View Ledger <ArrowRight size={14} />
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Group Modal */}
      <CreateGroupModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onCreated={fetchGroups}
      />
    </div>
  );
};

