import React, { useState, useEffect, useCallback } from 'react';
import { apiClient } from '../api/client';
import { useAuth } from '../context/AuthContext';
import { GroupExpenseModal } from './GroupExpenseModal';
import { SettleUpModal } from './SettleUpModal';
import { AddMemberModal } from './AddMemberModal';
import {
  ArrowLeft,
  Users,
  UserPlus,
  PlusCircle,
  CheckCircle,
  Receipt,
  DollarSign,
  TrendingDown,
  TrendingUp,
  ArrowRight,
  Calendar,
  Layers
} from 'lucide-react';

export const GroupDetailView = ({ groupId, onBack, categories = [] }) => {
  const { user } = useAuth();
  const [group, setGroup] = useState(null);
  const [expenses, setExpenses] = useState([]);
  const [balances, setBalances] = useState(null);
  const [settlements, setSettlements] = useState([]);
  const [activeTab, setActiveTab] = useState('expenses'); // 'expenses' or 'settlements'

  // Modals
  const [isExpenseModalOpen, setIsExpenseModalOpen] = useState(false);
  const [isSettleModalOpen, setIsSettleModalOpen] = useState(false);
  const [isAddMemberOpen, setIsAddMemberOpen] = useState(false);
  const [settlePreFill, setSettlePreFill] = useState({ payeeId: null, amount: '' });

  const fetchGroupData = useCallback(async () => {
    try {
      const [groupRes, expRes, balRes, setRes] = await Promise.all([
        apiClient.get(`/groups/${groupId}`),
        apiClient.get(`/groups/${groupId}/expenses`),
        apiClient.get(`/groups/${groupId}/balances`),
        apiClient.get(`/groups/${groupId}/settlements`),
      ]);
      setGroup(groupRes.data);
      setExpenses(expRes.data);
      setBalances(balRes.data);
      setSettlements(setRes.data);
    } catch (err) {
      console.error('Error fetching group data', err);
    }
  }, [groupId]);

  useEffect(() => {
    fetchGroupData();
  }, [fetchGroupData]);

  if (!group) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center', color: '#94a3b8' }}>
        Loading group ledger...
      </div>
    );
  }

  const handleOpenSettleDebt = (debt) => {
    setSettlePreFill({
      payeeId: debt.creditor_id,
      amount: debt.amount.toString(),
    });
    setIsSettleModalOpen(true);
  };

  const handleGeneralSettle = () => {
    setSettlePreFill({ payeeId: null, amount: '' });
    setIsSettleModalOpen(true);
  };

  return (
    <div>
      {/* Top Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        flexWrap: 'wrap',
        gap: '1rem',
        marginBottom: '1.5rem',
        paddingBottom: '1rem',
        borderBottom: '1px solid #334155'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button
            onClick={onBack}
            style={{
              background: '#1e293b',
              border: '1px solid #334155',
              color: '#94a3b8',
              borderRadius: '8px',
              padding: '8px 12px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <ArrowLeft size={16} /> Back
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontSize: '1.6rem', fontWeight: 800, margin: 0, color: '#f8fafc' }}>
                {group.name}
              </h1>
              <span style={{
                background: '#334155',
                color: '#818cf8',
                fontSize: '0.75rem',
                padding: '2px 8px',
                borderRadius: '6px',
                fontWeight: 600
              }}>
                {group.members.length} members
              </span>
              <span style={{
                background: '#064e3b',
                color: '#34d399',
                fontSize: '0.75rem',
                padding: '2px 8px',
                borderRadius: '6px',
                fontWeight: 600
              }}>
                Base: {group.currency || 'USD'}
              </span>
            </div>
            {group.description && (
              <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: '0.875rem' }}>
                {group.description}
              </p>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button
            onClick={() => setIsAddMemberOpen(true)}
            style={{
              background: '#1e293b',
              border: '1px solid #334155',
              color: '#f8fafc',
              padding: '8px 14px',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: 500,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <UserPlus size={16} color="#818cf8" />
            Add Member
          </button>

          <button
            onClick={handleGeneralSettle}
            style={{
              background: '#059669',
              border: 'none',
              color: '#ffffff',
              padding: '8px 16px',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <CheckCircle size={16} />
            Settle Up
          </button>

          <button
            onClick={() => setIsExpenseModalOpen(true)}
            style={{
              background: '#6366f1',
              border: 'none',
              color: '#ffffff',
              padding: '8px 16px',
              borderRadius: '8px',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <PlusCircle size={16} />
            Add Group Expense
          </button>
        </div>
      </div>

      {/* Summary Analytics & Simplified Debts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem', marginBottom: '2rem' }}>
        {/* Simplified Debts Box (Splitwise Algorithm Core) */}
        <div style={{
          background: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '12px',
          padding: '1.25rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, color: '#f8fafc' }}>
              <Layers size={18} color="#818cf8" />
              <span>Simplified Debts (Greedy Min-Max)</span>
            </div>
            <span style={{ fontSize: '0.75rem', background: '#312e81', color: '#c7d2fe', padding: '2px 6px', borderRadius: '4px' }}>
              Optimal
            </span>
          </div>

          {balances?.simplified_debts?.length === 0 ? (
            <div style={{ padding: '1.5rem', textAlign: 'center', color: '#10b981', fontSize: '0.9rem' }}>
              ✓ All debts are settled up! Everyone is even.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {balances?.simplified_debts?.map((debt, idx) => (
                <div
                  key={idx}
                  style={{
                    background: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    padding: '10px 12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '0.875rem'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span style={{ color: '#f87171', fontWeight: 600 }}>{debt.debtor_name}</span>
                    <span style={{ color: '#94a3b8' }}>owes</span>
                    <span style={{ color: '#10b981', fontWeight: 600 }}>{debt.creditor_name}</span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 700, color: '#f8fafc' }}>
                      ${parseFloat(debt.amount).toFixed(2)}
                    </span>
                    {debt.debtor_id === user?.id && (
                      <button
                        onClick={() => handleOpenSettleDebt(debt)}
                        style={{
                          background: '#10b981',
                          border: 'none',
                          color: '#ffffff',
                          padding: '4px 8px',
                          borderRadius: '6px',
                          fontSize: '0.75rem',
                          fontWeight: 600,
                          cursor: 'pointer'
                        }}
                      >
                        Pay
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Member Balances List */}
        <div style={{
          background: '#1e293b',
          border: '1px solid #334155',
          borderRadius: '12px',
          padding: '1.25rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, color: '#f8fafc' }}>
              <Users size={18} color="#818cf8" />
              <span>Member Standings</span>
            </div>
            <span style={{ fontSize: '0.85rem', color: '#94a3b8' }}>
              Total: ${parseFloat(balances?.total_spending || 0).toFixed(2)}
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {balances?.members?.map((m) => {
              const net = parseFloat(m.net_balance);
              return (
                <div
                  key={m.user_id}
                  style={{
                    background: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    padding: '8px 12px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    fontSize: '0.875rem'
                  }}
                >
                  <div>
                    <span style={{ color: '#f8fafc', fontWeight: 500 }}>
                      {m.full_name} {m.user_id === user?.id ? '(You)' : ''}
                    </span>
                    <span style={{ color: '#64748b', fontSize: '0.75rem', marginLeft: '6px' }}>
                      (Paid: ${parseFloat(m.total_paid).toFixed(2)})
                    </span>
                  </div>

                  <div>
                    {net > 0.001 ? (
                      <span style={{ color: '#10b981', fontWeight: 600 }}>
                        +${net.toFixed(2)} (gets back)
                      </span>
                    ) : net < -0.001 ? (
                      <span style={{ color: '#f87171', fontWeight: 600 }}>
                        -${Math.abs(net).toFixed(2)} (owes)
                      </span>
                    ) : (
                      <span style={{ color: '#94a3b8' }}>Settled</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Tabs: Shared Expenses vs Settlements */}
      <div style={{ display: 'flex', gap: '1rem', borderBottom: '1px solid #334155', marginBottom: '1.5rem' }}>
        <button
          onClick={() => setActiveTab('expenses')}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'expenses' ? '2px solid #6366f1' : '2px solid transparent',
            color: activeTab === 'expenses' ? '#818cf8' : '#94a3b8',
            padding: '8px 16px',
            fontSize: '0.95rem',
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          Shared Expenses ({expenses.length})
        </button>
        <button
          onClick={() => setActiveTab('settlements')}
          style={{
            background: 'transparent',
            border: 'none',
            borderBottom: activeTab === 'settlements' ? '2px solid #6366f1' : '2px solid transparent',
            color: activeTab === 'settlements' ? '#818cf8' : '#94a3b8',
            padding: '8px 16px',
            fontSize: '0.95rem',
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          Settlements History ({settlements.length})
        </button>
      </div>

      {/* Tab 1: Expenses Table */}
      {activeTab === 'expenses' && (
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ background: '#0f172a', color: '#94a3b8', borderBottom: '1px solid #334155' }}>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Date</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Description</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Paid By</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Split Strategy</th>
                <th style={{ padding: '12px 16px', fontWeight: 600, textAlign: 'right' }}>Total Amount</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Breakdown</th>
              </tr>
            </thead>
            <tbody>
              {expenses.length === 0 ? (
                <tr>
                  <td colSpan={6} style={{ padding: '2.5rem', textAlign: 'center', color: '#94a3b8' }}>
                    No group expenses yet. Click <strong>"Add Group Expense"</strong> to begin!
                  </td>
                </tr>
              ) : (
                expenses.map((exp) => (
                  <tr key={exp.id} style={{ borderBottom: '1px solid #33415540' }}>
                    <td style={{ padding: '12px 16px', color: '#94a3b8', whiteSpace: 'nowrap' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Calendar size={13} color="#64748b" />
                        {exp.expense_date}
                      </div>
                    </td>
                    <td style={{ padding: '12px 16px', color: '#f8fafc', fontWeight: 500 }}>
                      {exp.description}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#10b981', fontWeight: 600 }}>
                      {exp.payer?.full_name}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <span style={{
                        background: '#334155',
                        color: '#c7d2fe',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.75rem',
                        fontWeight: 600
                      }}>
                        {exp.split_type}
                      </span>
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 700, color: '#f8fafc' }}>
                      <div>{exp.currency || 'USD'} {parseFloat(exp.amount).toFixed(2)}</div>
                      {exp.currency && exp.currency !== (group.currency || 'USD') && exp.base_amount && (
                        <div style={{ fontSize: '0.75rem', color: '#38bdf8', fontWeight: 500 }}>
                          ≈ {group.currency || 'USD'} {parseFloat(exp.base_amount).toFixed(2)}
                        </div>
                      )}
                    </td>
                    <td style={{ padding: '12px 16px' }}>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                        {exp.splits.map((s) => (
                          <span
                            key={s.id}
                            style={{
                              background: '#0f172a',
                              border: '1px solid #334155',
                              padding: '2px 6px',
                              borderRadius: '4px',
                              fontSize: '0.75rem',
                              color: '#94a3b8'
                            }}
                          >
                            {s.user?.full_name?.split(' ')[0]}: {exp.currency || 'USD'} {parseFloat(s.owed_amount).toFixed(2)}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Tab 2: Settlements Table */}
      {activeTab === 'settlements' && (
        <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: '12px', overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
            <thead>
              <tr style={{ background: '#0f172a', color: '#94a3b8', borderBottom: '1px solid #334155' }}>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Date</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Payer</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Payee</th>
                <th style={{ padding: '12px 16px', fontWeight: 600, textAlign: 'right' }}>Amount</th>
                <th style={{ padding: '12px 16px', fontWeight: 600 }}>Notes</th>
              </tr>
            </thead>
            <tbody>
              {settlements.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ padding: '2.5rem', textAlign: 'center', color: '#94a3b8' }}>
                    No settlements recorded yet. Use <strong>"Settle Up"</strong> to pay off debts.
                  </td>
                </tr>
              ) : (
                settlements.map((s) => (
                  <tr key={s.id} style={{ borderBottom: '1px solid #33415540' }}>
                    <td style={{ padding: '12px 16px', color: '#94a3b8', whiteSpace: 'nowrap' }}>
                      {new Date(s.settled_at).toLocaleDateString()}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#f87171', fontWeight: 600 }}>
                      {s.payer?.full_name}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#10b981', fontWeight: 600 }}>
                      {s.payee?.full_name}
                    </td>
                    <td style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 700, color: '#f8fafc' }}>
                      ${parseFloat(s.amount).toFixed(2)}
                    </td>
                    <td style={{ padding: '12px 16px', color: '#94a3b8', fontSize: '0.85rem' }}>
                      {s.notes || '—'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Modals */}
      <GroupExpenseModal
        isOpen={isExpenseModalOpen}
        onClose={() => setIsExpenseModalOpen(false)}
        groupId={groupId}
        groupCurrency={group.currency || 'USD'}
        members={group.members}
        categories={categories}
        onSaved={fetchGroupData}
      />

      <SettleUpModal
        isOpen={isSettleModalOpen}
        onClose={() => setIsSettleModalOpen(false)}
        groupId={groupId}
        groupCurrency={group.currency || 'USD'}
        members={group.members}
        initialPayeeId={settlePreFill.payeeId}
        initialAmount={settlePreFill.amount}
        onSettled={fetchGroupData}
      />

      <AddMemberModal
        isOpen={isAddMemberOpen}
        onClose={() => setIsAddMemberOpen(false)}
        groupId={groupId}
        onMemberAdded={fetchGroupData}
      />
    </div>
  );
};

