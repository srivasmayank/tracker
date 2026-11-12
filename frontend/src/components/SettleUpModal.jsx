import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { X, CheckCircle, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const SettleUpModal = ({
  isOpen,
  onClose,
  groupId,
  groupCurrency = 'USD',
  members = [],
  initialPayeeId = null,
  initialAmount = '',
  onSettled
}) => {
  const { user } = useAuth();
  const [payeeId, setPayeeId] = useState('');
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [notes, setNotes] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (initialPayeeId) {
      setPayeeId(initialPayeeId);
    } else {
      const otherMembers = members.filter(m => m.user_id !== user?.id);
      if (otherMembers.length > 0) setPayeeId(otherMembers[0].user_id);
    }

    if (initialAmount) {
      setAmount(initialAmount);
    } else {
      setAmount('');
    }
    setCurrency(groupCurrency || 'USD');
    setNotes('');
    setError(null);
  }, [isOpen, initialPayeeId, initialAmount, members, user, groupCurrency]);

  if (!isOpen) return null;

  const eligiblePayees = members.filter(m => m.user_id !== user?.id);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      setError('Settlement amount must be greater than 0.');
      return;
    }

    if (!payeeId) {
      setError('Please select who you are paying.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      await apiClient.post(`/groups/${groupId}/settle`, {
        payee_id: parseInt(payeeId, 10),
        amount: parsedAmount,
        currency,
        notes: notes.trim() || null
      });
      onSettled();
      onClose();
    } catch (err) {
      const msg = err.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Failed to record settlement.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(15, 23, 42, 0.75)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 50,
      padding: '1rem'
    }}>
      <div style={{
        background: '#1e293b',
        border: '1px solid #334155',
        borderRadius: '16px',
        width: '100%',
        maxWidth: '440px',
        color: '#f8fafc',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        overflow: 'hidden'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid #334155'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <CheckCircle size={20} color="#10b981" />
            <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 600 }}>Settle Up Debt</h3>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '1.5rem' }}>
          {error && (
            <div style={{
              background: '#ef444420',
              border: '1px solid #ef4444',
              color: '#fca5a5',
              borderRadius: '8px',
              padding: '0.75rem',
              marginBottom: '1rem',
              fontSize: '0.85rem'
            }}>
              {error}
            </div>
          )}

          <div style={{
            background: '#0f172a',
            padding: '12px',
            borderRadius: '10px',
            border: '1px solid #334155',
            marginBottom: '1.25rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.9rem'
          }}>
            <div>
              <span style={{ color: '#94a3b8', fontSize: '0.8rem', display: 'block' }}>Payer</span>
              <span style={{ fontWeight: 600, color: '#f8fafc' }}>You ({user?.full_name})</span>
            </div>
            <ArrowRight size={18} color="#6366f1" />
            <div>
              <span style={{ color: '#94a3b8', fontSize: '0.8rem', display: 'block' }}>Payee</span>
              <span style={{ fontWeight: 600, color: '#10b981' }}>
                {members.find(m => m.user_id === parseInt(payeeId, 10))?.user?.full_name || 'Select recipient'}
              </span>
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
              Recipient (Who did you pay?) *
            </label>
            <select
              value={payeeId}
              onChange={(e) => setPayeeId(e.target.value)}
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
              {eligiblePayees.map((m) => (
                <option key={m.user_id} value={m.user_id}>
                  {m.user?.full_name} ({m.user?.email})
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
              Amount Paid & Currency *
            </label>
            <div style={{ display: 'flex', gap: '6px' }}>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                style={{
                  width: '85px',
                  background: '#0f172a',
                  border: '1px solid #334155',
                  color: '#34d399',
                  fontWeight: 700,
                  padding: '10px 6px',
                  borderRadius: '8px',
                  fontSize: '0.9rem',
                  outline: 'none'
                }}
              >
                <option value="USD">USD</option>
                <option value="EUR">EUR</option>
                <option value="GBP">GBP</option>
                <option value="INR">INR</option>
                <option value="CAD">CAD</option>
                <option value="AUD">AUD</option>
                <option value="JPY">JPY</option>
                <option value="CHF">CHF</option>
                <option value="SGD">SGD</option>
                <option value="AED">AED</option>
              </select>
              <input
                type="number"
                step="0.01"
                required
                placeholder="0.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                style={{
                  flex: 1,
                  boxSizing: 'border-box',
                  background: '#0f172a',
                  border: '1px solid #334155',
                  color: '#f8fafc',
                  padding: '10px 12px',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  outline: 'none'
                }}
              />
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
              Notes (e.g. Paid via Cash, Venmo, UPI)
            </label>
            <input
              type="text"
              placeholder="Optional payment reference"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              style={{
                width: '100%',
                boxSizing: 'border-box',
                background: '#0f172a',
                border: '1px solid #334155',
                color: '#f8fafc',
                padding: '10px 12px',
                borderRadius: '8px',
                fontSize: '0.9rem',
                outline: 'none'
              }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
            <button
              type="button"
              onClick={onClose}
              style={{
                background: '#334155',
                color: '#cbd5e1',
                border: 'none',
                padding: '10px 16px',
                borderRadius: '8px',
                cursor: 'pointer'
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              style={{
                background: '#10b981',
                color: '#ffffff',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 600
              }}
            >
              {loading ? 'Recording...' : 'Confirm Settle Up'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

