export type ImportRetailer = "lidl" | "rewe" | "dm" | "rossmann";

export interface ImportTechnicalError {
  error_code: number;
  detail: string;
}

export interface ImportProgressState {
  current: number;
  total: number;
  added: number;
  existing?: number;
  skipped: number;
  errors: number;
  items: number;
  current_receipt: string;
}

export interface ImportStartRequest {
  retailer: ImportRetailer;
  browser?: string | null;
  cookies_file?: string | null;
  customer_id?: string | null;
  user_login?: { email: string; password: string };
}

export interface ImportStartResponse {
  job_id: string;
  retailer: ImportRetailer;
}

export interface ImportJobEventPayload {
  job_id: string;
  retailer: ImportRetailer;
  status: "running" | "success" | "error";
  progress: ImportProgressState;
  error: ImportTechnicalError | null;
  message: string | null;
}
