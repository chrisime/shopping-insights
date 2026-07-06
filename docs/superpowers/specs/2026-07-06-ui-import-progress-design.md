# UI Import Progress Design

**Date:** 2026-07-06  
**Status:** Draft  
**Scope:** Start Lidl/REWE imports from the Vue dashboard and stream progress live via SSE

---

## 1. Goal

Add a dashboard action that can start a new receipt import without blocking the page.

The user must be able to:

- choose a retailer (`Lidl` or `REWE`)
- click one `Import` button
- watch the current import progress update live in the UI

The progress view should mirror the existing console progress state rather than inventing a separate model.

---

## 2. Product Decision

Use a **single active import job** per page, started by an API call and streamed back to the browser with SSE.

### Why this approach

- the page stays responsive
- the backend can reuse the existing workflow progress callbacks
- the UI can show the same metrics already printed in the terminal
- the feature stays small enough to fit the current dashboard layout

### UX shape

- retailer selector in the dashboard header or top control area
- one `Import` button next to it
- a progress bar and short status text beneath the controls
- the import control becomes disabled while a job is running

---

## 3. Scope

### In scope

- dashboard retailer selector for import target
- `Import` button in the Vue dashboard
- backend endpoint to start an import job asynchronously
- SSE endpoint to stream import job progress
- shared progress payload based on `workflows.progress_display.ProgressState`
- success and error terminal states in the UI

### Out of scope

- persistent job storage across restarts
- multi-job queueing
- cancel/retry controls
- changes to receipt parsing or workflow behavior
- polling fallback

---

## 4. Architecture

### Backend job layer

Add a small import-job service that:

- creates a job id
- runs the existing Lidl or REWE import workflow in a background worker
- collects progress events from the workflow callback
- exposes job state to SSE consumers

The job registry can stay in memory for now. That keeps the implementation simple and matches the current app lifecycle.
The backend may still track multiple jobs, but the Vue page should only start one active import at a time.

### API layer

Add two endpoints:

- `POST /imports/start` starts an import and returns a job id
- `GET /imports/{job_id}/events` streams job updates as SSE

### Frontend layer

Extend `DashboardPage.vue` with:

- a retailer select for import target selection
- an `Import` button
- a progress bar that reflects streamed job state
- status text for the current receipt and counters

---

## 5. Data Flow

1. User selects `Lidl` or `REWE`.
2. User clicks `Import`.
3. Vue sends `POST /imports/start` with the selected retailer.
4. Backend starts the import job in the background and returns `job_id` immediately.
5. Vue opens an `EventSource` to `GET /imports/{job_id}/events`.
6. Backend streams progress updates from the workflow callback.
7. Vue updates the progress bar and status text on each event.
8. When the job finishes, the stream sends a terminal event and the page refreshes dashboard data.

---

## 6. Progress Model

The streamed state should reuse the existing terminal model:

- `current`
- `total`
- `added`
- `skipped`
- `errors`
- `items`
- `current_receipt`

### UI rendering rules

- the bar should be determinate when `total > 0`
- the label should show `current/total` and percentage
- the secondary line should show the same counters as the console progress block
- the third line should show the current receipt id or a dash

This keeps the UI aligned with the import logs and avoids duplicate progress semantics.

---

## 7. Error Handling

### Start failures

If the import cannot be started, the `POST` endpoint should return a structured error and no SSE connection should be opened.

### Stream failures

If the job fails after it has started:

- the SSE stream should emit a terminal error event
- the UI should stop the progress state
- the UI should keep the retailer selection intact
- the UI should surface a short error message

### Unsupported states

If a browser reconnects to a missing or finished job id, the backend should respond with a clear not-found or terminal state instead of hanging.

---

## 8. Frontend Components

### `DashboardPage.vue`

Owns the import interaction state:

- selected retailer
- running job id
- streamed progress state
- error/success banners

It remains the orchestration layer and continues to own the existing dashboard refresh flow.

### Progress display

Add a compact progress block near the top controls:

- retailer select
- import button
- progress bar
- current receipt / counts text

The control should visually fit the existing dashboard shell and not require a separate page.

---

## 9. Backend Contract

### Start request

`POST /imports/start`

Request body:

```json
{
  "retailer": "lidl"
}
```

Response:

```json
{
  "job_id": "...",
  "retailer": "lidl"
}
```

### SSE stream

`GET /imports/{job_id}/events`

Events should carry a payload with:

- `type`: `progress` | `success` | `error`
- `state`: the progress snapshot when applicable
- `message`: human-readable terminal text when applicable

The exact wire format can follow the project’s existing JSON-in-strings pattern if that keeps the implementation simple.

---

## 10. Testing

### Backend tests

- starting an import returns a job id for Lidl and REWE
- progress callbacks are translated into stream events
- terminal success and error events are emitted
- missing job ids return a sensible error

### Frontend tests

- the dashboard renders the import selector and button
- clicking `Import` starts the job with the selected retailer
- streamed progress updates the visible state
- completion clears the running state and refreshes the dashboard

---

## 11. Non-Goals

- queueing multiple imports
- background job persistence
- live progress replay after reload
- upload-based imports
- changing the terminal progress display

---

## 12. Implementation Order

1. add the backend import job registry and SSE events
2. wire the existing Lidl/REWE workflows into the job layer
3. add the new import API routes
4. add the dashboard import controls and progress block
5. connect the frontend to the SSE stream
6. add tests for backend job flow and Vue rendering

---

## 13. Acceptance Criteria

- the dashboard has one import button and a Lidl/REWE selector
- starting an import does not block the page
- the UI shows live progress updates while the import runs
- the progress metrics match the existing console model
- Lidl and REWE imports both work through the same UI flow
