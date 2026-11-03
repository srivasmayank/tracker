import React from 'react';
import { Search, Edit2, Trash2, Calendar, CreditCard } from 'lucide-react';

export const ExpenseList = ({
  expenses,
  total,
  skip,
  limit,
  onPageChange,
  categories,
  selectedCategory,
  onCategoryFilterChange,
  searchQuery,
  onSearchChange,
  onEdit,
  onDelete,
  currency = 'USD'
}) => {
  return (
    <div style={{
      background: '#1e293b',
      border: '1px solid #334155',
      borderRadius: '12px',
      overflow: 'hidden'
    }}>
      {/* Table Controls (Search & Filter) */}
      <div style={{
        padding: '1.25rem',
        borderBottom: '1px solid #334155',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '1rem',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        {/* Search */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: '#0f172a',
          border: '1px solid #334155',
          borderRadius: '8px',
          padding: '8px 12px',
          flex: '1 1 260px',
          maxWidth: '380px'
        }}>
          <Search size={16} color="#94a3b8" />
          <input
            type="text"
            placeholder="Search expenses..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            style={{
              background: 'transparent',
              border: 'none',
              outline: 'none',
              color: '#f8fafc',
              fontSize: '0.9rem',
              width: '100%'
            }}
          />
        </div>

        {/* Category Filter */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>Filter:</span>
          <select
            value={selectedCategory}
            onChange={(e) => onCategoryFilterChange(e.target.value)}
            style={{
              background: '#0f172a',
              border: '1px solid #334155',
              borderRadius: '8px',
              padding: '8px 12px',
              color: '#f8fafc',
              fontSize: '0.875rem',
              outline: 'none'
            }}
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Table */}
      <div style={{ overflowX: 'auto' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
          <thead>
            <tr style={{ background: '#0f172a', color: '#94a3b8', borderBottom: '1px solid #334155' }}>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Date</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Description</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Category</th>
              <th style={{ padding: '12px 16px', fontWeight: 600 }}>Method</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, textAlign: 'right' }}>Amount</th>
              <th style={{ padding: '12px 16px', fontWeight: 600, textAlign: 'center' }}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {expenses.length === 0 ? (
              <tr>
                <td colSpan={6} style={{ padding: '2.5rem', textAlign: 'center', color: '#94a3b8' }}>
                  No expenses found. Click <strong>"Add Expense"</strong> to start recording!
                </td>
              </tr>
            ) : (
              expenses.map((expense) => (
                <tr
                  key={expense.id}
                  style={{
                    borderBottom: '1px solid #33415540',
                    transition: 'background 0.15s'
                  }}
                  onMouseOver={(e) => (e.currentTarget.style.background = '#33415530')}
                  onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
                >
                  <td style={{ padding: '12px 16px', color: '#94a3b8', whiteSpace: 'nowrap' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <Calendar size={14} color="#64748b" />
                      {expense.expense_date}
                    </div>
                  </td>
                  <td style={{ padding: '12px 16px', color: '#f8fafc', fontWeight: 500 }}>
                    {expense.description}
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '3px 8px',
                      borderRadius: '999px',
                      fontSize: '0.8rem',
                      fontWeight: 500,
                      background: `${expense.category?.color || '#6366f1'}20`,
                      color: expense.category?.color || '#818cf8',
                      border: `1px solid ${expense.category?.color || '#6366f1'}40`
                    }}>
                      <span style={{
                        width: '6px',
                        height: '6px',
                        borderRadius: '50%',
                        background: expense.category?.color || '#6366f1'
                      }} />
                      {expense.category?.name || 'Uncategorized'}
                    </span>
                  </td>
                  <td style={{ padding: '12px 16px' }}>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '4px',
                      color: '#94a3b8',
                      fontSize: '0.8rem'
                    }}>
                      <CreditCard size={13} />
                      {expense.payment_method}
                    </span>
                  </td>
                  <td style={{
                    padding: '12px 16px',
                    textAlign: 'right',
                    color: '#f8fafc',
                    fontWeight: 700,
                    fontSize: '0.95rem'
                  }}>
                    {currency} {parseFloat(expense.amount).toFixed(2)}
                  </td>
                  <td style={{ padding: '12px 16px', textAlign: 'center' }}>
                    <div style={{ display: 'flex', justifyContent: 'center', gap: '8px' }}>
                      <button
                        onClick={() => onEdit(expense)}
                        title="Edit Expense"
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#38bdf8',
                          cursor: 'pointer',
                          padding: '4px',
                          borderRadius: '4px'
                        }}
                      >
                        <Edit2 size={16} />
                      </button>
                      <button
                        onClick={() => onDelete(expense.id)}
                        title="Delete Expense"
                        style={{
                          background: 'transparent',
                          border: 'none',
                          color: '#f87171',
                          cursor: 'pointer',
                          padding: '4px',
                          borderRadius: '4px'
                        }}
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {total > limit && (
        <div style={{
          padding: '0.85rem 1.25rem',
          borderTop: '1px solid #334155',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.85rem',
          color: '#94a3b8'
        }}>
          <div>
            Showing {skip + 1} - {Math.min(skip + limit, total)} of {total} expenses
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              disabled={skip === 0}
              onClick={() => onPageChange(Math.max(0, skip - limit))}
              style={{
                background: '#0f172a',
                border: '1px solid #334155',
                color: skip === 0 ? '#475569' : '#f8fafc',
                padding: '6px 12px',
                borderRadius: '6px',
                cursor: skip === 0 ? 'not-allowed' : 'pointer'
              }}
            >
              Previous
            </button>
            <button
              disabled={skip + limit >= total}
              onClick={() => onPageChange(skip + limit)}
              style={{
                background: '#0f172a',
                border: '1px solid #334155',
                color: skip + limit >= total ? '#475569' : '#f8fafc',
                padding: '6px 12px',
                borderRadius: '6px',
                cursor: skip + limit >= total ? 'not-allowed' : 'pointer'
              }}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

