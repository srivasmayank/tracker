import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { X, Check, Users } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const GroupExpenseModal = ({
  isOpen,
  onClose,
  groupId,
  members = [],
  categories = [],
  onSaved
}) => {
  const { user } = useAuth();
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [expenseDate, setExpenseDate] = useState(new Date().toISOString().split('T')[0]);
  const [paidByUserId, setPaidByUserId] = useState('');
  const [splitType, setSplitType] = useState('EQUAL');

  // Participant split values keyed by user_id
  const [selectedParticipants, setSelectedParticipants] = useState({});
  const [exactAmounts, setExactAmounts] = useState({});
  const [percentages, setPercentages] = useState({});
  const [shares, setShares] = useState({});

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      setAmount('');
      setDescription('');
      if (categories.length > 0) setCategoryId(categories[0].id);
      setExpenseDate(new Date().toISOString().split('T')[0]);
      setPaidByUserId(user?.id || (members[0]?.user_id || ''));
      setSplitType('EQUAL');

      // Initialize all members as checked for equal split
      const initialSelected = {};
      const initialShares = {};
      members.forEach((m) => {
        initialSelected[m.user_id] = true;
        initialShares[m.user_id] = 1;
      });
      setSelectedParticipants(initialSelected);
      setShares(initialShares);
      setExactAmounts({});
      setPercentages({});
      setError(null);
    }
  }, [isOpen, members, categories, user]);

  if (!isOpen) return null;

  const toggleParticipant = (uid) => {
    setSelectedParticipants((prev) => ({
      ...prev,
      [uid]: !prev[uid],
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      setError('Amount must be greater than 0.');
      return;
    }

    if (!description.trim()) {
      setError('Description is required.');
      return;
    }

    let splitPayload = [];

    if (splitType === 'EQUAL') {
      const activeIds = Object.keys(selectedParticipants).filter((id) => selectedParticipants[id]);
      if (activeIds.length === 0) {
        setError('At least one member must be selected to split equally.');
        return;
      }
      splitPayload = activeIds.map((id) => ({ user_id: parseInt(id, 10) }));
    } else if (splitType === 'EXACT') {
      let sum = 0;
      for (const m of members) {
        const val = parseFloat(exactAmounts[m.user_id] || 0);
        if (val > 0) {
          sum += val;
          splitPayload.push({ user_id: m.user_id, owed_amount: val });
        }
      }
      if (Math.abs(sum - parsedAmount) > 0.001) {
        setError(`Sum of exact splits ($${sum.toFixed(2)}) must equal total expense ($${parsedAmount.toFixed(2)}).`);
        return;
      }
    } else if (splitType === 'PERCENTAGE') {
      let sumPct = 0;
      for (const m of members) {
        const val = parseFloat(percentages[m.user_id] || 0);
        if (val > 0) {
          sumPct += val;
          splitPayload.push({ user_id: m.user_id, percentage: val });
        }
      }
      if (Math.abs(sumPct - 100.0) > 0.01) {
        setError(`Sum of percentages (${sumPct}%) must equal exactly 100.00%.`);
        return;
      }
    } else if (splitType === 'SHARES') {
      for (const m of members) {
        const val = parseInt(shares[m.user_id] || 0, 10);
        if (val > 0) {
          splitPayload.push({ user_id: m.user_id, shares: val });
        }
      }
      if (splitPayload.length === 0) {
        setError('At least one member must have 1 or more shares.');
        return;
      }
    }

    setLoading(true);
    try {
      await apiClient.post(`/groups/${groupId}/expenses`, {
        category_id: parseInt(categoryId, 10),
        amount: parsedAmount,
        description: description.trim(),
        split_type: splitType,
        expense_date: expenseDate,
        paid_by_user_id: parseInt(paidByUserId, 10),
        splits: splitPayload,
      });

      onSaved();
      onClose();
    } catch (err) {
      const msg = err.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Failed to save group expense.');
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
        maxWidth: '520px',
        maxHeight: '90vh',
        color: '#f8fafc',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid #334155'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Users size={20} color="#818cf8" />
            <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 600 }}>Add Group Expense</h3>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {/* Scrollable Form */}
        <form onSubmit={handleSubmit} style={{ padding: '1.5rem', overflowY: 'auto' }}>
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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
                Total Amount *
              </label>
              <input
                type="number"
                step="0.01"
                required
                placeholder="0.00"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                style={{
                  width: '100%',
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

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
                Paid By *
              </label>
              <select
                value={paidByUserId}
                onChange={(e) => setPaidByUserId(e.target.value)}
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
                {members.map((m) => (
                  <option key={m.user_id} value={m.user_id}>
                    {m.user?.full_name} {m.user_id === user?.id ? '(You)' : ''}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
              Description *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Airbnb, Dinner at Trattoria"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1.25rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
                Category
              </label>
              <select
                value={categoryId}
                onChange={(e) => setCategoryId(e.target.value)}
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
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
                Date
              </label>
              <input
                type="date"
                required
                value={expenseDate}
                onChange={(e) => setExpenseDate(e.target.value)}
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
          </div>

          {/* Splitting Strategy Selector */}
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '8px' }}>
              Split Strategy
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px' }}>
              {['EQUAL', 'EXACT', 'PERCENTAGE', 'SHARES'].map((type) => (
                <button
                  key={type}
                  type="button"
                  onClick={() => setSplitType(type)}
                  style={{
                    padding: '8px 4px',
                    borderRadius: '8px',
                    fontSize: '0.8rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    border: splitType === type ? '1px solid #6366f1' : '1px solid #334155',
                    background: splitType === type ? '#6366f130' : '#0f172a',
                    color: splitType === type ? '#818cf8' : '#94a3b8'
                  }}
                >
                  {type === 'PERCENTAGE' ? '%' : type}
                </button>
              ))}
            </div>
          </div>

          {/* Dynamic Participant Breakdown */}
          <div style={{
            background: '#0f172a',
            border: '1px solid #334155',
            borderRadius: '10px',
            padding: '1rem',
            marginBottom: '1.5rem'
          }}>
            <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '10px', fontWeight: 600 }}>
              Participant Breakdown ({splitType})
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {members.map((m) => (
                <div key={m.user_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {splitType === 'EQUAL' && (
                      <input
                        type="checkbox"
                        checked={!!selectedParticipants[m.user_id]}
                        onChange={() => toggleParticipant(m.user_id)}
                        style={{ cursor: 'pointer', width: '16px', height: '16px' }}
                      />
                    )}
                    <span style={{ fontSize: '0.9rem', color: '#f8fafc' }}>{m.user?.full_name}</span>
                  </div>

                  {splitType === 'EXACT' && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>$</span>
                      <input
                        type="number"
                        step="0.01"
                        placeholder="0.00"
                        value={exactAmounts[m.user_id] || ''}
                        onChange={(e) => setExactAmounts({ ...exactAmounts, [m.user_id]: e.target.value })}
                        style={{
                          width: '90px',
                          background: '#1e293b',
                          border: '1px solid #334155',
                          color: '#f8fafc',
                          padding: '6px 8px',
                          borderRadius: '6px',
                          fontSize: '0.85rem',
                          textAlign: 'right'
                        }}
                      />
                    </div>
                  )}

                  {splitType === 'PERCENTAGE' && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <input
                        type="number"
                        step="0.01"
                        placeholder="0"
                        value={percentages[m.user_id] || ''}
                        onChange={(e) => setPercentages({ ...percentages, [m.user_id]: e.target.value })}
                        style={{
                          width: '75px',
                          background: '#1e293b',
                          border: '1px solid #334155',
                          color: '#f8fafc',
                          padding: '6px 8px',
                          borderRadius: '6px',
                          fontSize: '0.85rem',
                          textAlign: 'right'
                        }}
                      />
                      <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>%</span>
                    </div>
                  )}

                  {splitType === 'SHARES' && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <input
                        type="number"
                        step="1"
                        min="0"
                        value={shares[m.user_id] ?? 1}
                        onChange={(e) => setShares({ ...shares, [m.user_id]: e.target.value })}
                        style={{
                          width: '65px',
                          background: '#1e293b',
                          border: '1px solid #334155',
                          color: '#f8fafc',
                          padding: '6px 8px',
                          borderRadius: '6px',
                          fontSize: '0.85rem',
                          textAlign: 'right'
                        }}
                      />
                      <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>share(s)</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
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
                background: '#6366f1',
                color: '#ffffff',
                border: 'none',
                padding: '10px 20px',
                borderRadius: '8px',
                cursor: 'pointer',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <Check size={16} />
              {loading ? 'Saving...' : 'Save Group Expense'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

