export type DashboardFilters = {
  retailer?: string;
  start_date?: string;
  end_date?: string;
  time_granularity?: string;
  top_view?: string;
  top_limit?: number;
  search?: string;
  page?: number;
};

/** Retailer-specific KPI fields; the backend decides which keys are present. */
export type MetricsRow = Record<string, number>;

export type TimeSeriesRow = {
  period: string;
  total_spent: number;
  receipt_count: number;
  retailers?: string[];
};

export type Shopping = {
  weekday: number;
  weekday_name: string;
  trip_count: number;
  avg_spent: number;
  total_spent: number;
};

export type ShoppingItems = {
  name: string;
  total_quantity: number;
  total_spent: number;
  purchase_count: number;
  unit: string;
  total_count?: number;
  page?: number;
  page_size?: number;
};

export type DashboardSection =
  | { kind: "metrics"; title: string; items: MetricsRow[] }
  | { kind: "spending_over_time"; title: string; items: TimeSeriesRow[] }
  | { kind: "shopping"; title: string; items: Shopping[] }
  | { kind: "shopping_items"; title: string; items: ShoppingItems[] };

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

export type ReceiptAddress = {
  street?: string;
  street_no?: string;
  zip?: string;
  city?: string;
};

export type ReceiptItem = {
  name: string;
  quantity: number;
  unit: string;
  price: number;
  matched?: boolean;
};

export type ReceiptCoupon = {
  name: string;
  savings: number;
};

export type Receipt = {
  id: string;
  retailer: string;
  purchase_date: string;
  store?: string;
  address?: ReceiptAddress;
  total_price: number;
  items: ReceiptItem[];
  currency?: string;
  receipt_coupons?: ReceiptCoupon[];
};
