import React from 'react';
import Layout from '../components/layout';

const SavingsGoals: React.FC = () => {
  // Placeholder for future dynamic savings goals
  return (
    <Layout title="Savings Goals">
      <div className="max-w-4xl mx-auto py-8">
        <h1 className="text-3xl font-semibold mb-6">Savings Goals</h1>
        <p className="mb-4 text-gray-700">
          Track your savings goals and stay motivated to reach your financial targets.
        </p>

        <div className="bg-white shadow rounded p-6">
          <p className="text-gray-500 italic">Savings goals feature coming soon...</p>
        </div>
      </div>
    </Layout>
  );
};

export default SavingsGoals;
