const API_BASE_URL = 'http://localhost:8000/api';

export async function fetchAnalytics() {
  const response = await fetch(`${API_BASE_URL}/analytics`);
  if (!response.ok) {
    throw new Error('Failed to fetch analytics');
  }
  return response.json();
}

export async function syncEmails() {
  const response = await fetch(`${API_BASE_URL}/sync`, {
    method: 'POST',
  });
  if (!response.ok) {
    throw new Error('Failed to sync emails');
  }
  return response.json();
}
