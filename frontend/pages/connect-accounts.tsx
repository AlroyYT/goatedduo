import React, { useState } from 'react';

const ConnectAccounts: React.FC = () => {
  const [accountInfo, setAccountInfo] = useState({
    bankName: '',
    accountNumber: '',
    accountType: '',
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setAccountInfo({
      ...accountInfo,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setMessage(null);

    try {
      // Call your backend API to connect accounts here
      const response = await fetch('/api/connect-account', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(accountInfo),
      });

      if (response.ok) {
        setMessage('Account connected successfully!');
        setAccountInfo({ bankName: '', accountNumber: '', accountType: '' });
      } else {
        setMessage('Failed to connect account.');
      }
    } catch (error) {
      setMessage('Error connecting account.');
    }

    setIsSubmitting(false);
  };

  return (
    <div className="max-w-md mx-auto bg-white p-6 rounded shadow">
      <h1 className="text-2xl font-semibold mb-4">Connect Financial Account</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="bankName" className="block font-medium mb-1">
            Bank Name
          </label>
          <input
            type="text"
            id="bankName"
            name="bankName"
            value={accountInfo.bankName}
            onChange={handleChange}
            required
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <div>
          <label htmlFor="accountNumber" className="block font-medium mb-1">
            Account Number
          </label>
          <input
            type="text"
            id="accountNumber"
            name="accountNumber"
            value={accountInfo.accountNumber}
            onChange={handleChange}
            required
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <div>
          <label htmlFor="accountType" className="block font-medium mb-1">
            Account Type
          </label>
          <select
            id="accountType"
            name="accountType"
            value={accountInfo.accountType}
            onChange={handleChange}
            required
            className="w-full border rounded px-3 py-2"
          >
            <option value="" disabled>
              Select account type
            </option>
            <option value="checking">Checking</option>
            <option value="savings">Savings</option>
            <option value="investment">Investment</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {isSubmitting ? 'Connecting...' : 'Connect Account'}
        </button>
      </form>

      {message && <p className="mt-4 text-center">{message}</p>}
    </div>
  );
};

export default ConnectAccounts;
