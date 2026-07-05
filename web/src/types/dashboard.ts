export type DashboardSectionKind =
  | "metrics"
  | "bonus_rewe"
  | "bonus_lidl"
  | "bonus_total"
  | "time_series"
  | "weekday"
  | "top_items";

export interface DashboardFilters {
  retailer?: string;
  start_date?: string;
  end_date?: string;
  time_granularity?: string;
  spending_view?: string;
  top_view?: string;
  top_limit?: number;
}

export interface DashboardSection {
  kind: DashboardSectionKind;
  title: string;
  items: Array<Record<string, unknown>>;
}

export interface DashboardError {
  error_code: number;
  detail: string;
}

export interface DashboardPayload {
  title: string;
  sections: DashboardSection[];
  min_date?: string | null;
  max_date?: string | null;
  error?: DashboardError | null;
}
