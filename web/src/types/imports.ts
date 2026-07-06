export type ImportRetailer = "lidl" | "rewe";

export interface ImportProgressState {
  current: number;
  total: number;
  added: number;
  skipped: number;
  errors: number;
  items: number;
  current_receipt: string;
}

export interface ImportStartRequest {
  retailer: ImportRetailer;
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
  message: string | null;
}
