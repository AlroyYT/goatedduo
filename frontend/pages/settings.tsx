import React from 'react';
import Layout from '../components/layout';

const Settings: React.FC = () => {
  // Placeholder content, can be expanded with forms & API calls later
  return (
    <Layout title="Settings">
      <div className="max-w-4xl mx-auto py-8">
        <h1 className="text-3xl font-semibold mb-6">Account Settings</h1>
        <p className="mb-4 text-gray-700">
          Manage your account preferences, security settings, and notifications here.
        </p>

        <div className="bg-white shadow rounded p-6">
          <p className="text-gray-500 italic">Settings features coming soon...</p>
        </div>
      </div>
    </Layout>
  );
};

export default Settings;
