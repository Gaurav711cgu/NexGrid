const API_BASE = '/api';

export async function request(endpoint, options = {}) {
  const token = localStorage.getItem('nexagrid_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Network request failed' }));
    throw new Error(errorData.detail || 'An unexpected error occurred');
  }

  return res.json();
}

export const api = {
  register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login: (data) => request('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  getMe: () => request('/auth/me'),
  createRoom: (data) => request('/rooms', { method: 'POST', body: JSON.stringify(data) }),
  getRoomByCode: (code) => request(`/rooms/${code}`),
  getRoomHistory: (roomId, cursor = null) => request(`/rooms/${roomId}/history${cursor ? `?cursor=${cursor}` : ''}`),
  getRoomAnalytics: (roomId) => request(`/analytics/room/${roomId}/summary`),
  executeCode: (roomId, data) => request(`/execution/${roomId}/run`, { method: 'POST', body: JSON.stringify(data) }),
};
