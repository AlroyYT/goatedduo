import React, { useState } from 'react';
import Head from 'next/head';
import Navbar from './Navbar';
import Sidebar from './Sidebar';

interface LayoutProps {
  children: React.ReactNode;
  title?: string;
}

const Layout: React.FC<LayoutProps> = ({ children, title = 'Financial Advisor' }) => {
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);
  
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <>
      <Head>
        <title>{title} | AI Financial Advisor</title>
        <meta name="description" content="AI-powered personalized financial advice platform" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <div className="layout-wrapper">
        <Navbar toggleSidebar={toggleSidebar} />
        
        <div className="content-area">
          <Sidebar isOpen={sidebarOpen} />
          
          <main className="main-content">
            <div className="container">
              {children}
            </div>
          </main>
        </div>
      </div>
    </>
  );
};

export default Layout;
