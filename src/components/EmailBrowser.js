import React, { useState, useEffect } from 'react';
import { format } from 'date-fns';

export default function EmailBrowser() {
  const [emails, setEmails] = useState([]);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(50);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [afterDate, setAfterDate] = useState('');
  const [sortBy, setSortBy] = useState('domain_frequency');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchTerm);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchTerm]);

  useEffect(() => {
    fetchEmails();
  }, [page, debouncedSearch, afterDate, sortBy]);

  const fetchEmails = async () => {
    setIsLoading(true);
    try {
      const searchParams = new URLSearchParams({
        page: page,
        page_size: pageSize,
        sort_by: sortBy,
        ...(debouncedSearch && { search: debouncedSearch }),
        ...(afterDate && { after_date: afterDate })
      });

      const response = await fetch(`http://localhost:8000/api/emails?${searchParams}`);
      if (!response.ok) throw new Error('Failed to fetch emails');
      
      const data = await response.json();
      setEmails(data.emails);
      setTotal(data.total);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-4">
      {/* Controls */}
      <div className="flex flex-col space-y-4 sm:flex-row sm:justify-between sm:items-center sm:space-y-0 sm:space-x-4">
        <h2 className="text-2xl font-bold">Emails</h2>
        <div className="flex flex-col space-y-2 sm:flex-row sm:space-y-0 sm:space-x-4">
          <input
            type="text"
            placeholder="Search emails..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="px-4 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="date"
            value={afterDate}
            onChange={(e) => setAfterDate(e.target.value)}
            className="px-4 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="pr-8 py-2 rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
          <option value="domain_frequency">Domain</option>
          <option value="sender_frequency">Sender</option>
          <option value="date">DateDate</option>
          </select>
        </div>
      </div>

      {/* Loading and Error States */}
      {isLoading && (
        <div className="text-center py-4">
          <div className="text-gray-500">Loading...</div>
        </div>
      )}

      {error && (
        <div className="bg-red-50 text-red-700 p-4 rounded-md">
          {error}
        </div>
      )}

      {/* Pagination */}
      <div className="flex items-center justify-between px-4 py-3 bg-white rounded-lg shadow">
        <div>
          <p className="text-sm text-gray-700">
            Showing <span className="font-medium">{((page - 1) * pageSize) + 1}</span> to{' '}
            <span className="font-medium">{Math.min(page * pageSize, total)}</span> of{' '}
            <span className="font-medium">{total}</span> results
          </p>
        </div>
        <div>
          <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
            >
              Next
            </button>
          </nav>
        </div>
      </div>

      {/* Email List */}
      <div className="bg-white shadow overflow-hidden rounded-lg">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Sender
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Subject
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Date
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {emails.map((email) => (
                <tr key={email.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">{email.sender_name}</div>
                    <div className="text-sm text-gray-500">{email.sender_email}</div>
                  </td>
                  <td className="px-6 py-4">
                    <div className="text-sm text-gray-900">{email.subject}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {email.received_date && format(new Date(email.received_date), 'MMM d, yyyy HH:mm')}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
