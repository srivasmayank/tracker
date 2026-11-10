import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api/client';
import { Repeat, Plus, Play, Trash2, Calendar, CheckCircle2, Clock, DollarSign } from 'lucide-react';

export const RecurringView = ({ categories = [], onExpenseCreated }) => {
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [batchResult, setBatchResult] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);

  // Form State
  const [formData, setFormData] = useState({
    category_id: categories[0]?.id || '',
    amount: '',
    description: '',
    frequency: 'MONTHLY',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    payment_method: 'CARD'
  });

  const fetchSubscriptions = useCallback(async () => {
    setLoading(true);
    try {
      const res = await apiClient.get('/recurring');
      setSubscriptions(res.data);
    } catch (err) {
      console.error('Failed to load recurring subscriptions', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSubscriptions();
  }, [fetchSubscriptions]);

  const handleProcessDue = async () => {
    setIsProcessing(true);
    setBatchResult(null);
    try {
      const res = await apiClient.post('/recurring/process-due');
      setBatchResult(res.data);
      fetchSubscriptions();
      if (onExpenseCreated) onExpenseCreated();
    } catch (err) {
      alert('Error triggering recurring expense batch.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this recurring subscription rule?')) return;
    try {
      await apiClient.delete(`/recurring/${id}`);
      fetchSubscriptions();
    } catch (err) {
      alert('Failed to delete subscription rule.');
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        category_id: parseInt(formData.category_id || categories[0]?.id),
        amount: parseFloat(formData.amount),
        description: formData.description.trim(),
        frequency: formData.frequency,
        start_date: formData.start_date,
        end_date: formData.end_date || null,
        payment_method: formData.payment_method
      };
      await apiClient.post('/recurring', payload);
      setShowAddModal(false);
      setFormData({
        category_id: categories[0]?.id || '',
        amount: '',
        description: '',
        frequency: 'MONTHLY',
        start_date: new Date().toISOString().split('T')[0],
        end_date: '',
        payment_method: 'CARD'
      });
      fetchSubscriptions();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to register recurring subscription.');
    }
  };

  return (
    <div>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.5rem'
      }}>
        <div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 800, margin: 0, letterSpacing: '-0.02em' }}>
            Recurring Subscriptions & Automation
          </h1>
          <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: '0.9rem' }}>
            Schedule periodic expenses (Netflix, Rent, SIPs) and automate statement generation via background workers.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={handleProcessDue}
            disabled={isProcessing}
            style={{
              background: '#047857',
              color: '#ffffff',
              border: 'none',
              padding: '10px 16px',
              borderRadius: '8px',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: isProcessing ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 6px -1px rgba(4, 120, 87, 0.4)'
            }}
          >
            <Play size={16} />
            {isProcessing ? 'Processing Engine...' : 'Run Due Engine Now'}
          </button>

          <button
            onClick={() => setShowAddModal(true)}
            style={{
              background: '#6366f1',
              color: '#ffffff',
              border: 'none',
              padding: '10px 16px',
              borderRadius: '8px',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              boxShadow: '0 4px 6px -1px rgba(99, 102, 241, 0.4)'
            }}
          >
            <Plus size={18} />
            Add Subscription
          </button>
        </div>
      </div>

      {/* Batch Result Notification */}
      {batchResult && (
        <div style={{
          background: '#064e3b',
          border: '1px solid #059669',
          color: '#d1fae5',
          borderRadius: '10px',
          padding: '12px 16px',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <CheckCircle2 size={20} color="#34d399" />
          <div style={{ fontSize: '0.9rem' }}>
            <strong>Automation Batch Executed:</strong> Generated <strong>{batchResult.processed_count}</strong> expenses for due date {batchResult.target_date}. ({batchResult.failed_count} failed).
          </div>
        </div>
      )}

      {/* Subscriptions Grid */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: '#94a3b8' }}>Loading subscriptions...</div>
      ) : subscriptions.length === 0 ? (
        <div style={{
          background: '#1e293b',
          border: '1px dashed #334155',
          borderRadius: '12px',
          padding: '3rem',
          textAlign: 'center',
          color: '#94a3b8'
        }}>
          <Repeat size={40} color="#6366f1" style={{ margin: '0 auto 1rem' }} />
          <h3 style={{ margin: '0 0 8px', color: '#f8fafc' }}>No Recurring Subscriptions Configured</h3>
          <p style={{ margin: '0 0 1.5rem', fontSize: '0.9rem' }}>
            Add Netflix, Gym membership, or Rent to have expenses generated automatically on their due dates.
          </p>
          <button
            onClick={() => setShowAddModal(true)}
            style={{
              background: '#6366f1',
              color: '#ffffff',
              border: 'none',
              padding: '8px 16px',
              borderRadius: '8px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Configure First Subscription
          </button>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1rem' }}>
          {subscriptions.map((sub) => (
            <div
              key={sub.id}
              style={{
                background: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '12px',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}
            >
              <div>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <span style={{
                    fontSize: '0.75rem',
                    background: sub.is_active ? '#064e3b' : '#334155',
                    color: sub.is_active ? '#34d399' : '#94a3b8',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontWeight: 700
                  }}>
                    {sub.is_active ? 'ACTIVE' : 'INACTIVE'}
                  </span>

                  <span style={{
                    fontSize: '0.75rem',
                    background: '#312e81',
                    color: '#c7d2fe',
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontWeight: 600
                  }}>
                    {sub.frequency}
                  </span>
                </div>

                <h3 style={{ margin: '0 0 4px', fontSize: '1.15rem', color: '#f8fafc' }}>{sub.description}</h3>
                <div style={{ fontSize: '1.5rem', fontWeight: 800, color: '#38bdf8', marginBottom: '12px' }}>
                  ${parseFloat(sub.amount).toFixed(2)}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.825rem', color: '#94a3b8' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Calendar size={14} />
                    <span>Next Due: <strong style={{ color: '#f8fafc' }}>{sub.next_due_date}</strong></span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <Clock size={14} />
                    <span>Category: <strong>{sub.category?.name || 'General'}</strong></span>
                  </div>
                </div>
              </div>

              <div style={{
                marginTop: '1.25rem',
                paddingTop: '0.75rem',
                borderTop: '1px solid #334155',
                display: 'flex',
                justifyContent: 'flex-end'
              }}>
                <button
                  onClick={() => handleDelete(sub.id)}
                  title="Delete subscription"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: '#f87171',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '0.8rem'
                  }}
                >
                  <Trash2 size={15} />
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Subscription Modal */}
      {showAddModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '1rem',
          backdropFilter: 'blur(4px)'
        }}>
          <div style={{
            background: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '480px',
            padding: '1.75rem',
            color: '#f8fafc'
          }}>
            <h3 style={{ margin: '0 0 1rem', fontSize: '1.25rem' }}>Add Recurring Subscription</h3>
            <form onSubmit={handleCreate} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div>
                <label style={{ fontSize: '0.85rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                  Description / Service Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Netflix, Gym, Rent"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  style={{
                    width: '100%',
                    background: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    padding: '10px',
                    color: '#f8fafc',
                    boxSizing: 'border-box'
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.85rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                    Amount
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    placeholder="0.00"
                    value={formData.amount}
                    onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                    style={{
                      width: '100%',
                      background: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      padding: '10px',
                      color: '#f8fafc',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '0.85rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                    Frequency
                  </label>
                  <select
                    value={formData.frequency}
                    onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                    style={{
                      width: '100%',
                      background: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      padding: '10px',
                      color: '#f8fafc',
                      boxSizing: 'border-box'
                    }}
                  >
                    <option value="DAILY">Daily</option>
                    <option value="WEEKLY">Weekly</option>
                    <option value="MONTHLY">Monthly</option>
                    <option value="YEARLY">Yearly</option>
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div>
                  <label style={{ fontSize: '0.85rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                    Category
                  </label>
                  <select
                    value={formData.category_id}
                    onChange={(e) => setFormData({ ...formData, category_id: e.target.value })}
                    style={{
                      width: '100%',
                      background: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      padding: '10px',
                      color: '#f8fafc',
                      boxSizing: 'border-box'
                    }}
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '0.85rem', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>
                    Start Date
                  </label>
                  <input
                    type="date"
                    required
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    style={{
                      width: '100%',
                      background: '#0f172a',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      padding: '10px',
                      color: '#f8fafc',
                      boxSizing: 'border-box'
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '1rem' }}>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  style={{
                    background: 'transparent',
                    border: '1px solid #334155',
                    color: '#94a3b8',
                    padding: '8px 16px',
                    borderRadius: '8px',
                    cursor: 'pointer'
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  style={{
                    background: '#6366f1',
                    color: '#ffffff',
                    border: 'none',
                    padding: '8px 18px',
                    borderRadius: '8px',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  Save Subscription
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
