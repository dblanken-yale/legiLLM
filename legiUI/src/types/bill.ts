export interface Bill {
  bill_id: string;
  bill_number: string;
  title: string;
  url: string;
  state?: string;
  year?: string | number;
  session?: string;
  is_relevant: boolean;
  relevance_reasoning?: string;
  summary?: string;
  bill_status?: string;
  legislation_type?: string;
  categories?: string[];
  tags?: string[];
  key_provisions?: string[];
  palliative_care_impact?: string;
  exclusion_check?: string;
  special_flags?: string[];
  status_date?: string;
  last_action?: string;
  similarity_score?: number;
  distance?: number;
}

export interface FilterState {
  states: string[];
  categories: string[];
  years: string[];
  statuses: string[];
  legislationTypes: string[];
  searchQuery: string;
}

export interface DashboardStats {
  totalBills: number;
  byState: Record<string, number>;
  byCategory: Record<string, number>;
  byYear: Record<string, number>;
  byStatus: Record<string, number>;
  byLegislationType: Record<string, number>;
}
