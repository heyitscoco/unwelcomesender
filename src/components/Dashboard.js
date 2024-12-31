import React, { useState, useEffect } from 'react';
import TopSenders from './TopSenders';
import TopDomains from './TopDomains';
import { fetchAnalytics, syncEmails } from '../services/api';

function Dashboard() {
  const [analytics, setAnalytics] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const data = await fetchAnalytics();
      setAnalytics(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSync = async () => {
    setIsLoading(true);
    try {
      await syncEmails();
      await loadAnalytics();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  if (error) {
    return (
      <div className="rounded-md bg-red-50 p-4 mt-4">
        <div className="text-red-700">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button
          onClick={handleSync}
          disabled={isLoading}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-indigo-300"
        >
          {isLoading ? 'Syncing...' : 'Sync Emails'}
        </button>
      </div>

      {analytics && (
        <div className="space-y-6">
          <TopSenders data={analytics.top_senders} />
          <TopDomains data={analytics.top_domains} />
        </div>
      )}
    </div>
  );
}

export default Dashboard;
