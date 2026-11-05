import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../api/client';
import { Navbar } from '../components/Navbar';
import { SpendingCharts } from '../components/SpendingCharts';
import { ExpenseList } from '../components/ExpenseList';
import { ExpenseModal } from '../components/ExpenseModal';
import { GroupsView } from '../components/GroupsView';
import { PlusCircle, RefreshCw } from 'lucide-react';

export const Dashboard = () => {
  const { user } = useAuth();
  const [currentTab, setCurrentTab] = useState('personal'); // 'personal' or 'groups'

  // Personal Expenses State
  const [expenses, setExpenses] = useState([]);
  const [total, setTotal] = useState(0);
  const [skip, setSkip] = useState(0);
  const [limit] = useState(25);
  const [categories, setCategories] = useState([]);
  const [summary, setSummary] = useState(null);

  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [expenseToEdit, setExpenseToEdit] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch Categories
  const fetchCategories = useCallback(async () => {
    try {
      const res = await apiClient.get('/categories');
      setCategories(res.data);
    } catch (err) {
      console.error('Failed to load categories', err);
    }
  }, []);

  // Fetch Summary Analytics
  const fetchSummary = useCallback(async () => {
    try {
      const res = await apiClient.get('/expenses/summary');
      setSummary(res.data);
    } catch (err) {
      console.error('Failed to load summary', err);
    }
  }, []);

  // Fetch Paginated Expenses
  const fetchExpenses = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        skip,
        limit,
      };
      if (selectedCategory) params.category_id = selectedCategory;
      if (searchQuery.trim()) params.search = searchQuery.trim();

      const res = await apiClient.get('/expenses', { params });
      setExpenses(res.data.items);
      setTotal(res.data.total);
    } catch (err) {
      console.error('Failed to load expenses', err);
    } finally {
      setLoading(false);
    }
  }, [skip, limit, selectedCategory, searchQuery]);

  // Initial load
  useEffect(() => {
    fetchCategories();
    fetchSummary();
  }, [fetchCategories, fetchSummary]);

  // Refetch when filters/pagination change
  useEffect(() => {
    if (currentTab === 'personal') {
      fetchExpenses();
    }
  }, [fetchExpenses, currentTab]);

  const handleEdit = (expense) => {
    setExpenseToEdit(expense);
    setIsModalOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this expense?')) return;
    try {
      await apiClient.delete(`/expenses/${id}`);
      fetchExpenses();
      fetchSummary();
    } catch (err) {
      alert('Failed to delete expense.');
    }
  };

  const handleSaved = () => {
    fetchExpenses();
    fetchSummary();
  };

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0f172a',
      color: '#f8fafc',
      fontFamily: 'Inter, system-ui, -apple-system, sans-serif'
    }}>
      <Navbar currentTab={currentTab} onTabChange={setCurrentTab} />

      <main style={{ maxWidth: '1240px', margin: '0 auto', padding: '2rem 1.5rem' }}>
        {currentTab === 'groups' ? (
          <GroupsView categories={categories} />
        ) : (
          <>
            {/* Top Action Header */}
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
                  Personal Expenses
                </h1>
                <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: '0.9rem' }}>
                  Track daily spending, categorize transactions, and inspect financial metrics.
                </p>
              </div>

              <div style={{ display: 'flex', gap: '0.75rem' }}>
                <button
                  onClick={() => {
                    fetchSummary();
                    fetchExpenses();
                  }}
                  title="Refresh Data"
                  style={{
                    background: '#1e293b',
                    border: '1px solid #334155',
                    color: '#94a3b8',
                    padding: '10px 14px',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <RefreshCw size={16} />
                </button>

                <button
                  onClick={() => {
                    setExpenseToEdit(null);
                    setIsModalOpen(true);
                  }}
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
                  Add Expense
                </button>
              </div>
            </div>

            {/* Analytics & Metrics */}
            <SpendingCharts summary={summary} currency={user?.currency || 'USD'} />

            {/* Expense Transactions Table */}
            <ExpenseList
              expenses={expenses}
              total={total}
              skip={skip}
              limit={limit}
              onPageChange={setSkip}
              categories={categories}
              selectedCategory={selectedCategory}
              onCategoryFilterChange={(val) => {
                setSelectedCategory(val);
                setSkip(0);
              }}
              searchQuery={searchQuery}
              onSearchChange={(val) => {
                setSearchQuery(val);
                setSkip(0);
              }}
              onEdit={handleEdit}
              onDelete={handleDelete}
              currency={user?.currency || 'USD'}
            />

            {/* Add / Edit Expense Modal */}
            <ExpenseModal
              isOpen={isModalOpen}
              onClose={() => setIsModalOpen(false)}
              onSaved={handleSaved}
              expenseToEdit={expenseToEdit}
              categories={categories}
            />
          </>
        )}
      </main>
    </div>
  );
};
