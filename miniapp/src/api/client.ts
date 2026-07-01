let _initDataRaw = '';

export function setInitData(raw: string) {
  _initDataRaw = raw;
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`/api${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `tma ${_initDataRaw}`,
      ...options.headers,
    },
  });

  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      msg = body?.detail?.error || body?.detail || body?.error || msg;
    } catch {}
    throw new Error(msg);
  }

  return res.json();
}

const get = <T>(path: string) => request<T>(path);
const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: 'POST', body: JSON.stringify(body) });
const patch = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: 'PATCH', body: JSON.stringify(body) });
const del = <T>(path: string) => request<T>(path, { method: 'DELETE' });

export const api = {
  me: () => get<import('./types').User>('/me'),

  dashboard: (period = 'week') =>
    get<import('./types').DashboardData>(`/dashboard?period=${period}`),

  tasks: {
    list: (status = 'all') => get<import('./types').Task[]>(`/tasks?status=${status}`),
    create: (body: Record<string, unknown>) => post<import('./types').Task>('/tasks', body),
    update: (id: number, body: Record<string, unknown>) =>
      patch<import('./types').Task>(`/tasks/${id}`, body),
    delete: (id: number) => del<{ ok: boolean }>(`/tasks/${id}`),
  },

  tenders: {
    list: (rating = 'all') => get<import('./types').Tender[]>(`/tenders?rating=${rating}`),
    get: (number: string) => get<import('./types').Tender>(`/tenders/${encodeURIComponent(number)}`),
    take: (number: string, assignee_id?: number) =>
      post<import('./types').Tender>(`/tenders/${encodeURIComponent(number)}/take`, { assignee_id }),
    refresh: () => post<{ ok: boolean; tenders_available: number }>('/tenders/refresh'),
  },

  team: (period = 'week') =>
    get<{ members: import('./types').TeamMember[]; top3: import('./types').TeamMember[] }>(
      `/team?period=${period}`
    ),

  employee: (id: number) => get<import('./types').TeamMember>(`/employees/${id}`),

  analytics: (period = 'week') =>
    get<import('./types').AnalyticsData>(`/analytics?period=${period}`),

  notifications: {
    list: () => get<import('./types').Notification[]>('/notifications'),
    unreadCount: () => get<{ count: number }>('/notifications/unread-count'),
    markRead: (ids?: number[]) =>
      post<{ ok: boolean }>('/notifications/read', { ids: ids || [] }),
  },

  admin: {
    pending: () => get<import('./types').User[]>('/admin/pending'),
    users: () => get<import('./types').User[]>('/admin/users'),
    approve: (id: number) => post<{ ok: boolean }>(`/admin/users/${id}/approve`),
    reject: (id: number) => post<{ ok: boolean }>(`/admin/users/${id}/reject`),
    block: (id: number) => post<{ ok: boolean }>(`/admin/users/${id}/block`),
    setRole: (id: number, role: string) =>
      patch<{ ok: boolean }>(`/admin/users/${id}/role`, { role }),
  },
};
