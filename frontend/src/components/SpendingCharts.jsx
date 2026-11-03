import React from 'react';
import { DollarSign, Receipt, PieChart, TrendingUp } from 'lucide-react';

export const SpendingCharts = ({ summary, currency = 'USD' }) => {
  if (!summary) return null;

  const topCategory = summary.categories?.length > 0
    ? [...summary.categories].sort((a, b) => parseFloat(b.total_amount) - parseFloat(a.total_amount))[0]
    : null;

  return (
    <div style={{ marginBottom: '2rem' }}>
      {/* KPI Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '1.25rem',
        marginBottom: '1.5rem'
      }}>
        <div style={{
          background: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '12px',
          padding: '1.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <div style={{
            background: '#10b98120',
            border: '1px solid #10b98140',
            borderRadius: '10px',
            padding: '12px',
            color: '#10b981'
          }}>
            <DollarSign size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>
              Total Spending
            </div>
            <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#f8fafc' }}>
              {currency} {parseFloat(summary.total_spent || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </div>
          </div>
        </div>

        <div style={{
          background: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '12px',
          padding: '1.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <div style={{
            background: '#6366f120',
            border: '1px solid #6366f140',
            borderRadius: '10px',
            padding: '12px',
            color: '#818cf8'
          }}>
            <Receipt size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>
              Transactions
            </div>
            <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#f8fafc' }}>
              {summary.total_transactions || 0}
            </div>
          </div>
        </div>

        <div style={{
          background: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '12px',
          padding: '1.25rem',
          display: 'flex',
          alignItems: 'center',
          gap: '1rem'
        }}>
          <div style={{
            background: '#f59e0b20',
            border: '1px solid #f59e0b40',
            borderRadius: '10px',
            padding: '12px',
            color: '#f59e0b'
          }}>
            <TrendingUp size={24} />
          </div>
          <div>
            <div style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>
              Top Category
            </div>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f8fafc' }}>
              {topCategory ? topCategory.category_name : 'N/A'}
            </div>
            {topCategory && (
              <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                {topCategory.percentage}% of total
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Category Breakdown Progress Bars */}
      {summary.categories?.length > 0 && (
        <div style={{
          background: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '12px',
          padding: '1.5rem'
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            marginBottom: '1.25rem',
            color: '#f8fafc',
            fontWeight: 600
          }}>
            <PieChart size={18} color="#818cf8" />
            <span>Category Spending Breakdown</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {summary.categories.map((cat) => (
              <div key={cat.category_id}>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  marginBottom: '6px',
                  fontSize: '0.875rem'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      background: cat.category_color || '#6366f1'
                    }} />
                    <span style={{ color: '#f8fafc', fontWeight: 500 }}>{cat.category_name}</span>
                  </div>
                  <div style={{ color: '#94a3b8' }}>
                    <span style={{ color: '#f8fafc', fontWeight: 600 }}>
                      {currency} {parseFloat(cat.total_amount).toFixed(2)}
                    </span>
                    {' '}({cat.percentage}%)
                  </div>
                </div>

                {/* Progress bar track */}
                <div style={{
                  height: '8px',
                  background: '#0f172a',
                  borderRadius: '999px',
                  overflow: 'hidden'
                }}>
                  <div style={{
                    height: '100%',
                    width: `${Math.min(cat.percentage, 100)}%`,
                    background: cat.category_color || '#6366f1',
                    borderRadius: '999px',
                    transition: 'width 0.5s ease-in-out'
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

