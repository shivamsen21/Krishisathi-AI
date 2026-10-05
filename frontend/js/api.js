/* ============================================================
   AgroVision AI — api.js
   Centralized API Client and Auth Session Utilities
   ============================================================ */

const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8000';

const AgroVisionAPI = {
  getToken() {
    return localStorage.getItem('agrovision_token') || '';
  },

  setToken(token) {
    if (token) localStorage.setItem('agrovision_token', token);
    else localStorage.removeItem('agrovision_token');
  },

  getUser() {
    try {
      const raw = localStorage.getItem('agrovision_user');
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  setUser(user) {
    if (user) localStorage.setItem('agrovision_user', JSON.stringify(user));
    else localStorage.removeItem('agrovision_user');
  },

  clearAuth() {
    localStorage.removeItem('agrovision_token');
    localStorage.removeItem('agrovision_user');
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  isAdmin() {
    const user = this.getUser();
    return user && user.role === 'admin';
  },

  async request(endpoint, options = {}) {
    const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
    const headers = { ...options.headers };

    // Inject Bearer token if present
    const token = this.getToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    // Set JSON content-type if body is an object and not FormData
    if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
      if (typeof options.body === 'object') {
        options.body = JSON.stringify(options.body);
      }
    }

    try {
      const res = await fetch(url, { ...options, headers });
      let data = null;
      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        data = await res.json();
      } else {
        data = await res.text();
      }

      if (!res.ok) {
        const errorMsg = (data && (data.detail || data.message)) || `Request failed with status ${res.status}`;
        const error = new Error(errorMsg);
        error.status = res.status;
        error.data = data;
        throw error;
      }

      return data;
    } catch (err) {
      // If unauthorized on protected route, handle gracefully
      if (err.status === 401 && !endpoint.includes('/api/auth/login')) {
        console.warn('Session expired or unauthorized. Clearing session.');
        this.clearAuth();
      }
      throw err;
    }
  },

  // Auth endpoints
  async register(fullName, email, password) {
    const data = await this.request('/api/auth/register', {
      method: 'POST',
      body: { full_name: fullName, email, password }
    });
    if (data.access_token) {
      this.setToken(data.access_token);
      this.setUser(data.user);
    }
    return data;
  },

  async login(email, password) {
    const data = await this.request('/api/auth/login', {
      method: 'POST',
      body: { email, password }
    });
    if (data.access_token) {
      this.setToken(data.access_token);
      this.setUser(data.user);
    }
    return data;
  },

  async logout() {
    try {
      await this.request('/api/auth/logout', { method: 'POST' });
    } catch {
      // Ignore network errors on logout
    } finally {
      this.clearAuth();
    }
  },

  async getMe() {
    const user = await this.request('/api/auth/me');
    this.setUser(user);
    return user;
  },

  async updateProfile(updates) {
    const user = await this.request('/api/auth/profile', {
      method: 'PUT',
      body: updates
    });
    this.setUser(user);
    return user;
  },

  async forgotPassword(email) {
    return await this.request('/api/auth/forgot-password', {
      method: 'POST',
      body: { email }
    });
  },

  // Prediction & Diseases
  async predict(imageFile, crop) {
    const formData = new FormData();
    formData.append('image', imageFile);
    if (crop) formData.append('crop', crop);
    return await this.request('/api/predict', {
      method: 'POST',
      body: formData
    });
  },

  async getDiseases(crop) {
    const query = crop ? `?crop=${encodeURIComponent(crop)}` : '';
    return await this.request(`/api/diseases${query}`);
  },

  // History
  async getHistory(params = {}) {
    const q = new URLSearchParams();
    if (params.limit) q.set('limit', params.limit);
    if (params.offset) q.set('offset', params.offset);
    if (params.crop) q.set('crop', params.crop);
    if (params.status) q.set('status', params.status);
    const queryString = q.toString() ? `?${q.toString()}` : '';
    return await this.request(`/api/history${queryString}`);
  },

  async getHistoryDetail(id) {
    return await this.request(`/api/history/${id}`);
  },

  // Assistant / Chat
  async chat(message, crop) {
    return await this.request('/api/chat', {
      method: 'POST',
      body: { message, crop }
    });
  },

  async getAdminStats() {
    return await this.request('/api/admin/stats');
  },

  async getAdminUsers() {
    return await this.request('/api/admin/users');
  },

  async getAdminPredictions() {
    return await this.request('/api/admin/predictions');
  },

  // Admin Disease CRUD
  async createDisease(diseaseData) {
    return await this.request('/api/admin/diseases', {
      method: 'POST',
      body: diseaseData
    });
  },

  async updateDisease(id, updates) {
    return await this.request(`/api/admin/diseases/${id}`, {
      method: 'PUT',
      body: updates
    });
  },

  async deleteDisease(id) {
    return await this.request(`/api/admin/diseases/${id}`, {
      method: 'DELETE'
    });
  },

  async getDiseaseById(id) {
    return await this.request(`/api/diseases/${id}`);
  }
};

window.AgroVisionAPI = AgroVisionAPI;
