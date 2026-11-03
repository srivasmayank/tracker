import React, { useState, useEffect } from 'react';
import { apiClient } from '../api/client';
import { X, Check } from 'lucide-react';

export const ExpenseModal = ({ isOpen, onClose, onSaved, expenseToEdit, categories }) => {
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [categoryId, setCategoryId] = useState('');
  const [expenseDate, setExpenseDate] = useState(new Date().toISOString().split('T')[0]);
  const [paymentMethod, setPaymentMethod] = useState('CARD');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (expenseToEdit) {
      setAmount(expenseToEdit.amount);
      setDescription(expenseToEdit.description);
      setCategoryId(expenseToEdit.category_id);
      setExpenseDate(expenseToEdit.expense_date);
      setPaymentMethod(expenseToEdit.payment_method);
    } else {
      setAmount('');
      setDescription('');
      if (categories.length > 0) {
        setCategoryId(categories[0].id);
      }
      setExpenseDate(new Date().toISOString().split('T')[0]);
      setPaymentMethod('CARD');
    }
    setError(null);
  }, [expenseToEdit, categories, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);

    const parsedAmount = parseFloat(amount);
    if (isNaN(parsedAmount) || parsedAmount <= 0) {
      setError('Amount must be strictly greater than 0.');
      return;
    }

    if (!description.trim()) {
      setError('Please provide a description.');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        amount: parsedAmount,
        description: description.trim(),
        category_id: parseInt(categoryId, 10),
        expense_date: expenseDate,
        payment_method: paymentMethod,
      };

      if (expenseToEdit) {
        await apiClient.put(`/expenses/${expenseToEdit.id}`, payload);
      } else {
        await apiClient.post('/expenses', payload);
      }

      onSaved();
      onClose();
    } catch (err) {
      const msg = err.response?.data?.detail;
      setError(typeof msg === 'string' ? msg : 'Failed to save expense. Please verify inputs.');
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
        maxWidth: '480px',
        color: '#f8fafc',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
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
          <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 600 }}>
            {expenseToEdit ? 'Edit Expense' : 'Add New Expense'}
          </h3>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              padding: '4px'
            }}
          >
            <X size={20} />
          </button>
        </div>

        {/* Form Body */}
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

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
              Amount
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

          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
              Description
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Weekly grocery run"
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

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
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

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.85rem', color: '#94a3b8', marginBottom: '6px' }}>
              Payment Method
            </label>
            <select
              value={paymentMethod}
              onChange={(e) => setPaymentMethod(e.target.value)}
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
              <option value="CARD">Credit / Debit Card</option>
              <option value="CASH">Cash</option>
              <option value="UPI">UPI / Digital Wallet</option>
              <option value="TRANSFER">Bank Transfer</option>
              <option value="OTHER">Other</option>
            </select>
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
                cursor: 'pointer',
                fontWeight: 500
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
              {loading ? 'Saving...' : expenseToEdit ? 'Update Expense' : 'Save Expense'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

