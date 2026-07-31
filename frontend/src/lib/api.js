const API_BASE = '/api';

export async function request(endpoint, options = {}) {
  let token = localStorage.getItem('nexagrid_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...options.headers,
  };

  let res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  // Automatic Refresh Token Rotation on 401 Unauthorized
  if (res.status === 401 && endpoint !== '/auth/login' && endpoint !== '/auth/refresh') {
    try {
      const refreshRes = await fetch(`${API_BASE}/auth/refresh`, { method: 'POST' });
      if (refreshRes.ok) {
        const refreshData = await refreshRes.json();
        localStorage.setItem('nexagrid_token', refreshData.access_token);
        headers['Authorization'] = `Bearer ${refreshData.access_token}`;
        
        // Retry original request with new token
        res = await fetch(`${API_BASE}${endpoint}`, {
          ...options,
          headers,
        });
      }
    } catch (e) {
      localStorage.removeItem('nexagrid_token');
    }
  }

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Network request failed' }));
    throw new Error(errorData.detail || 'An unexpected error occurred');
  }

  return res.json();
}

export const api = {
  register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  login: (data) => request('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  logout: () => request('/auth/logout', { method: 'POST' }),
  refreshToken: () => request('/auth/refresh', { method: 'POST' }),
  getMe: () => request('/auth/me'),
  createRoom: (data) => request('/rooms', { method: 'POST', body: JSON.stringify(data) }),
  getRoomByCode: (code) => request(`/rooms/${code}`),
  getRoomHistory: (roomId, cursor = null) => request(`/rooms/${roomId}/history${cursor ? `?cursor=${cursor}` : ''}`),
  getRoomAnalytics: (roomId) => request(`/analytics/room/${roomId}/summary`),
  executeCode: (roomId, data) => request(`/execution/${roomId}/run`, { method: 'POST', body: JSON.stringify(data) }),
};
