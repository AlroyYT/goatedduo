import Layout from '../components/layout';
import FinancialSummary from '../components/Dashboard/FinancialSummary';
import RecentTransactions from '../components/Dashboard/RecentTransactions';
import SpendingChart from '../components/Dashboard/SpendingChart';

export default function DashboardPage() {
  const summaryData = {
    income: 5500,
    expenses: 3000,
    savings: 1200,
  };

  const transactions = [
    { id: '1', date: '2025-05-01', description: 'Groceries', amount: -150 },
    { id: '2', date: '2025-05-02', description: 'Salary', amount: 5000 },
    { id: '3', date: '2025-05-03', description: 'Utilities', amount: -100 },
  ];

  const spendingData = [
    { category: 'Rent', value: 1200 },
    { category: 'Food', value: 450 },
    { category: 'Transport', value: 300 },
    { category: 'Entertainment', value: 200 },
  ];

  return (
    <Layout>
      <h2 className="text-2xl font-bold mb-4">Dashboard</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <FinancialSummary {...summaryData} />
        <SpendingChart data={spendingData} />
      </div>
      <RecentTransactions transactions={transactions} />
    </Layout>
  );
}
