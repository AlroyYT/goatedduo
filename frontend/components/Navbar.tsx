import React from 'react';
import Link from 'next/link';

interface NavbarProps {
  toggleSidebar: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ toggleSidebar }) => {
  return (
    <nav className="bg-white shadow">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Left side - Logo and menu button */}
          <div className="flex items-center">
            <button 
              onClick={toggleSidebar}
              className="mr-4 text-gray-500 hover:text-gray-700 focus:outline-none hide-desktop"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
            
            <Link href="/" className="flex items-center">
              <img src="/images/logo.png" alt="FinanceAI Logo" className="h-8 w-auto" />
              <span className="ml-2 font-semibold text-lg text-primary">FinanceAI</span>
            </Link>
          </div>
          
          {/* Center - Navigation (Hidden on mobile) */}
          <div className="hidden md:flex items-center space-x-4">
            <Link href="/dashboard" className="px-3 py-2 text-gray-700 hover:text-primary">
              Dashboard
            </Link>
            <Link href="/budget-planner" className="px-3 py-2 text-gray-700 hover:text-primary">
              Budget
            </Link>
            <Link href="/investment-advice" className="px-3 py-2 text-gray-700 hover:text-primary">
              Investments
            </Link>
            <Link href="/savings-goals" className="px-3 py-2 text-gray-700 hover:text-primary">
              Goals
            </Link>
            <Link href="/reports" className="px-3 py-2 text-gray-700 hover:text-primary">
              Reports
            </Link>
          </div>
          
          {/* Right side - User menu */}
          <div className="flex items-center">
            {/* Notifications */}
            <button className="p-1 rounded-full text-gray-500 hover:text-primary focus:outline-none">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </button>
            
            {/* User menu */}
            <div className="ml-4 relative flex items-center">
              <div className="flex items-center">
                <div className="h-8 w-8 rounded-full bg-primary flex items-center justify-center text-white font-semibold">
                  JD
                </div>
                <div className="ml-2 text-sm hide-mobile">
                  <span className="block font-medium text-gray-700">John Doe</span>
                  <span className="block text-xs text-gray-500">Premium Account</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
