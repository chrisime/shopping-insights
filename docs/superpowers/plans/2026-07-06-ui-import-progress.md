# UI Import Progress Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Start Lidl/REWE imports from the Vue dashboard without blocking the page, and stream the existing workflow progress live over SSE.

**Architecture:** Add a small in-memory backend job registry that wraps the existing retailer workflows and publishes progress snapshots. Expose a start endpoint plus an SSE event stream, then add a Vue composable and control block that opens the stream, renders progress, and refreshes the dashboard when the job finishes.

**Tech Stack:** FastAPI, `StreamingResponse`, `threading`, `queue`, `ProgressState`, Vue 3, `EventSource`, Oruga, Tailwind, pytest, Vitest

## Global Constraints

- the page should not block
- use SSE instead of polling for progress
- there should be one button `Import` and a Lidl/REWE selection option in the dashboard UI
- the progress view should mirror the existing console progress state
- the backend job registry can stay in memory for now
- no persistent job storage across restarts
- no multi-job queueing
- no polling fallback
- do not change the terminal progress display

---

## File Structure

- `api/services/import_job_service.py`: in-memory import job registry, background worker, and job state accessors
- `api/services/trigger_service.py`: re-export import job helpers so the existing `tests/test_import_jobs.py` path still works
- `api/schemas/imports.py`: request/response models for the new import endpoints
- `api/routes/imports.py`: `POST /imports/start` and `GET /imports/{job_id}/events`
- `api/main.py`: register the new imports router
- `web/src/types/imports.ts`: import job request, progress, and SSE payload types
- `web/src/api/imports.ts`: start-job request and EventSource URL helper
- `web/src/composables/useImportJob.ts`: import state, SSE lifecycle, and dashboard refresh hook
- `web/src/components/ImportJobControls.vue`: import button, retailer selector, and progress bar
- `web/src/components/DashboardPage.vue`: place the import control into the page shell
- `tests/test_import_jobs.py`: backend job registry tests
- `tests/test_api_imports.py`: API start and SSE route tests
- `web/src/api/imports.spec.ts`: frontend request helper tests
- `web/src/composables/__tests__/useImportJob.spec.ts`: SSE state transition tests
- `web/src/components/__tests__/ImportJobControls.spec.ts`: control rendering and interaction tests
- `web/src/components/__tests__/DashboardPageImport.spec.ts`: page integration test for the import flow

---

### Task 1: Backend import job registry

**Files:**
- Create: `api/services/import_job_service.py`
- Modify: `api/services/trigger_service.py`
- Modify: `tests/test_import_jobs.py`

**Interfaces:**
- Consumes: `workflows.lidl_workflow.run_lidl_initial`, `workflows.rewe_workflow.run_rewe_initial`, `workflows.progress_display.ProgressState`
- Produces: `start_import_job(retailer: str) -> str`, `get_import_job(job_id: str) -> ImportJobSnapshot | None`, and a small in-memory snapshot model with `status`, `progress`, and `message`

- [ ] **Step 1: Write the failing test**

```python
def test_start_import_job_tracks_progress(monkeypatch):
    from api.services import trigger_service
    import time
    from workflows.progress_display import ProgressState

    def fake_run_lidl_initial(*, browser=None, cookies_file=None, country=None, output_dir=None, progress_listener=None):
        if progress_listener is not None:
            progress_listener(ProgressState(current=0, total=1, added=0, skipped=0, errors=0, items=0, current_receipt="-"))
            progress_listener(ProgressState(current=1, total=1, added=1, skipped=0, errors=0, items=3, current_receipt="r1"))
        return True

    monkeypatch.setattr(trigger_service, "run_lidl_initial", fake_run_lidl_initial)

    job_id = trigger_service.start_import_job("lidl")
    deadline = time.time() + 2
    state = None
    while time.time() < deadline:
        state = trigger_service.get_import_job(job_id)
        if state is not None and state.status != "running":
            break
        time.sleep(0.01)

    assert state is not None
    assert state.status == "success"
    assert state.progress.current == 1
    assert state.progress.current_receipt == "r1"
```

Add a second test that calls `trigger_service.start_import_job("rewe")` with a fake REWE workflow and a third test that `get_import_job("missing") is None`.

- [ ] **Step 2: Run the test to confirm it fails**

Run: `./.venv/bin/python -m pytest -q tests/test_import_jobs.py`
Expected: fail because the job helpers do not exist yet.

- [ ] **Step 3: Implement the minimal backend registry**

```python
@dataclass
class ImportJobSnapshot:
    job_id: str
    retailer: str
    status: Literal["running", "success", "error"]
    progress: ProgressState
    message: str | None = None

def start_import_job(retailer: str) -> str: ...
def get_import_job(job_id: str) -> ImportJobSnapshot | None: ...
```

Use a `threading.Thread` per job plus a shared dict keyed by job id. Update the snapshot from the workflow `progress_listener` callback so the console output and UI state stay aligned.

Re-export `start_import_job` and `get_import_job` from `api/services/trigger_service.py` so the current test module keeps importing the same service boundary.

- [ ] **Step 4: Run the test to confirm it passes**

Run: `./.venv/bin/python -m pytest -q tests/test_import_jobs.py`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add api/services/import_job_service.py api/services/trigger_service.py tests/test_import_jobs.py
git commit -m "feat: add import job registry"
```

### Task 2: Import API and SSE stream

**Files:**
- Create: `api/schemas/imports.py`
- Create: `api/routes/imports.py`
- Modify: `api/main.py`
- Add: `tests/test_api_imports.py`

**Interfaces:**
- Consumes: `api.services.import_job_service.start_import_job`, `api.services.import_job_service.get_import_job`, `api.services.import_job_service.iter_import_job_events`
- Produces: `POST /imports/start` and `GET /imports/{job_id}/events`

- [ ] **Step 1: Write the failing test**

```python
def test_import_start_returns_job_id(monkeypatch):
    from fastapi.testclient import TestClient
    from api.main import app
    from api.services import import_job_service

    monkeypatch.setattr(import_job_service, "start_import_job", lambda retailer: "job-1")

    response = TestClient(app).post("/imports/start", json={"retailer": "lidl"})

    assert response.status_code == 200
    assert response.json() == {"job_id": "job-1", "retailer": "lidl"}
```

Add a streaming test that patches `iter_import_job_events("job-1")` to yield one progress event and one success event, then assert the response body contains `event: progress` and `event: success`.

- [ ] **Step 2: Run the test to confirm it fails**

Run: `./.venv/bin/python -m pytest -q tests/test_api_imports.py`
Expected: fail because the route and schema do not exist yet.

- [ ] **Step 3: Implement the route and SSE framing**

Use Pydantic models for the request and response body, then return a `StreamingResponse` with `media_type="text/event-stream"`.

```python
@router.post("/start", response_model=ImportStartResponse)
def start_import(payload: ImportStartRequest) -> ImportStartResponse: ...

@router.get("/{job_id}/events")
def import_events(job_id: str):
    return StreamingResponse(stream_import_job_events(job_id), media_type="text/event-stream")
```

Format each SSE frame as a named event with JSON data so the frontend can use `EventSource.addEventListener("progress", ...)`.

- [ ] **Step 4: Run the test to confirm it passes**

Run: `./.venv/bin/python -m pytest -q tests/test_api_imports.py`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add api/schemas/imports.py api/routes/imports.py api/main.py tests/test_api_imports.py
git commit -m "feat: add import sse api"
```

### Task 3: Frontend import request helpers and composable

**Files:**
- Create: `web/src/types/imports.ts`
- Create: `web/src/api/imports.ts`
- Create: `web/src/composables/useImportJob.ts`
- Add: `web/src/api/imports.spec.ts`
- Add: `web/src/composables/__tests__/useImportJob.spec.ts`

**Interfaces:**
- Consumes: `fetch`, `EventSource`, `DashboardFilters`-style runtime patterns from the existing Vue code
- Produces: `startImportJob(retailer: ImportRetailer): Promise<ImportStartResponse>`, `openImportJobEvents(jobId: string): EventSource`, and `useImportJob(refreshDashboard: () => Promise<void> | void)`

- [ ] **Step 1: Write the failing test**

```ts
it("starts an import job for the selected retailer", async () => {
  const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ job_id: "job-1", retailer: "lidl" }) });
  vi.stubGlobal("fetch", fetchMock);

  await startImportJob("lidl");

  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(String(fetchMock.mock.calls[0][0])).toContain("/imports/start");
});
```

Add a composable test that mocks `EventSource`, emits `progress` and `success`, and asserts that `progress.value` updates and `refreshDashboard()` is called once on success.

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `corepack pnpm test -- --run web/src/api/imports.spec.ts web/src/composables/__tests__/useImportJob.spec.ts`
Expected: fail because the helper and composable do not exist yet.

- [ ] **Step 3: Implement the API helpers and composable**

```ts
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
```

The composable should keep one `EventSource` instance at a time, close any previous stream before starting a new one, and clear the connection on unmount.

- [ ] **Step 4: Run the tests to confirm they pass**

Run: `corepack pnpm test -- --run web/src/api/imports.spec.ts web/src/composables/__tests__/useImportJob.spec.ts`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add web/src/types/imports.ts web/src/api/imports.ts web/src/composables/useImportJob.ts web/src/api/imports.spec.ts web/src/composables/__tests__/useImportJob.spec.ts
git commit -m "feat: add frontend import stream client"
```

### Task 4: Dashboard import controls and page integration

**Files:**
- Create: `web/src/components/ImportJobControls.vue`
- Modify: `web/src/components/DashboardPage.vue`
- Add: `web/src/components/__tests__/ImportJobControls.spec.ts`
- Add: `web/src/components/__tests__/DashboardPageImport.spec.ts`

**Interfaces:**
- Consumes: `useDashboard()`, `useImportJob()`, and the import types from `web/src/types/imports.ts`
- Produces: a visible `Import` button, retailer selector, and determinate progress bar in the dashboard header area

- [ ] **Step 1: Write the failing test**

```ts
it("shows the import selector, button, and progress text", async () => {
  const wrapper = mount(ImportJobControls, {
    props: {
      retailer: "lidl",
      running: false,
      progress: { current: 1, total: 3, added: 1, skipped: 0, errors: 0, items: 4, current_receipt: "r1" },
      message: null,
      error: null,
    },
    global: { plugins: [Oruga] },
  });

  expect(wrapper.text()).toContain("Import");
  expect(wrapper.text()).toContain("1/3");
  expect(wrapper.text()).toContain("r1");
});
```

Add a page-level test that mocks the composable and asserts the page renders the control and calls `startImport()` when the button is clicked.

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `corepack pnpm test -- --run web/src/components/__tests__/ImportJobControls.spec.ts web/src/components/__tests__/DashboardPageImport.spec.ts`
Expected: fail because the component and wiring do not exist yet.

- [ ] **Step 3: Implement the UI wiring**

Render `ImportJobControls.vue` near the page header, bind it to the composable state, and trigger a dashboard refresh after a successful import stream closes.

Keep the export button and dashboard filters unchanged so the import flow is an additive change.

- [ ] **Step 4: Run the tests to confirm they pass**

Run: `corepack pnpm test -- --run web/src/components/__tests__/ImportJobControls.spec.ts web/src/components/__tests__/DashboardPageImport.spec.ts web/src/components/__tests__/DashboardPage.spec.ts`
Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add web/src/components/ImportJobControls.vue web/src/components/DashboardPage.vue web/src/components/__tests__/ImportJobControls.spec.ts web/src/components/__tests__/DashboardPageImport.spec.ts
git commit -m "feat: add dashboard import controls"
```

### Task 5: End-to-end verification

**Files:**
- No new files expected

**Interfaces:**
- Consumes: the full import backend + Vue UI flow
- Produces: verified build and test results

- [ ] **Step 1: Run backend tests**

Run: `./.venv/bin/python -m pytest -q tests/test_import_jobs.py tests/test_api_imports.py`
Expected: pass.

- [ ] **Step 2: Run frontend tests**

Run: `corepack pnpm test -- --run web/src/api/imports.spec.ts web/src/composables/__tests__/useImportJob.spec.ts web/src/components/__tests__/ImportJobControls.spec.ts web/src/components/__tests__/DashboardPageImport.spec.ts web/src/components/__tests__/DashboardPage.spec.ts`
Expected: pass.

- [ ] **Step 3: Run the frontend build**

Run: `corepack pnpm build`
Expected: pass.

- [ ] **Step 4: Commit any final verification-only adjustments**

```bash
git add -A
git commit -m "test: verify import progress flow"
```

---

## Self-Review

- spec coverage: backend job registry, SSE route, frontend client, composable, UI control, and verification are all mapped to tasks
- placeholder scan: no TBD/TODO placeholders remain
- type consistency: `ProgressState` is the source of truth for streamed progress, and `start_import_job` / `get_import_job` are used consistently across backend tasks
- scope check: this is one feature slice, not multiple independent subsystems
