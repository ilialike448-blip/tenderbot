export interface User {
  telegram_id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  role: 'admin' | 'lead' | 'member';
  status: 'pending' | 'approved' | 'rejected' | 'blocked';
  position?: string;
  color: string;
  initials: string;
}

export interface Task {
  id: number;
  title: string;
  status: 'new' | 'in_work' | 'review' | 'done';
  priority: 'low' | 'med' | 'high';
  assignee_id?: number;
  assignee_first?: string;
  assignee_last?: string;
  assignee_color?: string;
  co_assignees: number[];
  tender_number?: string;
  tender_name?: string;
  due_date?: string;
  progress_pct: number;
  time_spent_min: number;
  time_estimate_min?: number;
  created_at: string;
  closed_at?: string;
}

export interface Tender {
  external_number: string;
  name: string;
  nmc?: number;
  customer?: string;
  region?: string;
  rating?: 'fire' | 'ok' | 'warn';
  margin_percent?: number;
  cost_estimate?: number;
  analysis_text?: string;
  analyzed_at?: string;
  portal_status?: 'free' | 'in_work' | 'submitted' | 'won' | 'lost' | 'skipped';
  assigned_to?: number;
  assignee_first?: string;
  assignee_last?: string;
  assignee_color?: string;
  taken_at?: string;
  taken_by_name?: string;
  law?: string;
  delivery_days?: number;
  federal_district?: string;
  cert_requirements?: string[];
  typical_participants?: number;
  source_url?: string;
  url?: string;
}

export interface TeamMember {
  telegram_id: number;
  first_name: string;
  last_name?: string;
  username?: string;
  role: string;
  position?: string;
  color: string;
  initials: string;
  is_active: boolean;
  done: number;
  in_work: number;
  new_count: number;
  tenders_count: number;
  active_tender_num?: string;
  active_tender_name?: string;
}

export interface Notification {
  id: number;
  user_id: number;
  type: string;
  text: string;
  is_read: number;
  created_at: string;
  link?: string;
}

export interface DashboardData {
  summary: { done: number; in_work: number; new: number };
  team: TeamMember[];
  processes: Array<{
    id: number; title: string; status: string;
    due_date?: string; first_name?: string; last_name?: string;
  }>;
  tenders_in_work: Tender[];
}

export interface AnalyticsData {
  period: string;
  summary: {
    tenders_taken: number;
    ai_found: number;
    total_sum: number;
    total_cost: number;
    profit_forecast?: number;
    margin_pct?: number;
  };
  per_tender: Array<Tender & { profit?: number; assignee_name?: string }>;
}

export interface ApiError {
  error: string;
  code: number;
}
