import React from 'react';
import Link from 'next/link';
import Layout from '../components/layout';

const Home: React.FC = () => {
  return (
    <Layout title="Home">
      <div className="text-center py-20">
        <h1 className="text-4xl font-bold mb-4">Welcome to AI Financial Advisor</h1>
        <p className="text-lg mb-8">
          Get personalized financial advice and manage your money smarter.
        </p>
        <div className="space-x-4">
          <Link href="/signup" legacyBehavior>
            <a className="px-6 py-3 bg-blue-600 text-white rounded hover:bg-blue-700">
              Get Started
            </a>
          </Link>
          <Link href="/signin" legacyBehavior>
            <a className="px-6 py-3 border border-blue-600 text-blue-600 rounded hover:bg-blue-100">
              Sign In
            </a>
          </Link>
        </div>
      </div>
    </Layout>
  );
};

export default Home;
