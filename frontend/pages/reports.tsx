import React from 'react';
import Layout from '../components/layout';

const Reports: React.FC = () => {
  // Placeholder data could be replaced with API data later
  return (
    <Layout title="Financial Reports">
      <div className="max-w-4xl mx-auto py-8">
        <h1 className="text-3xl font-semibold mb-6">Financial Reports</h1>
        <p className="mb-4 text-gray-700">
          Here you can view your detailed financial reports, including spending patterns,
          income summaries, investment performance, and more.
        </p>

        <div className="bg-white shadow rounded p-6">
          <p className="text-gray-500 italic">Reports functionality coming soon...</p>
        </div>
      </div>
    </Layout>
  );
};

export default Reports;
