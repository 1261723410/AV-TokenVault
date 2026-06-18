# AV-TokenVault MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a local macOS-friendly AV-TokenVault MVP with a Python/FastAPI backend, Next.js/shadcn UI, SQLite persistence, mock embeddings, and clear extension points for real encoders and vector stores.

**Architecture:** The backend owns uploads, media extraction, encoding, job state, file serving, and SQLite persistence. The frontend is a single workbench page that talks to the backend through typed API helpers. Portability comes from explicit configuration, conda environment files, isolated `data/` paths, and adapter interfaces for encoders and vector storage.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, Pydantic Settings, pytest, httpx/TestClient, FFmpeg subprocess calls, Next.js, TypeScript, Tailwind, shadcn/ui, SQLite.

---

## File Map

Backend files:

- `backend/pyproject.toml`: Python project metadata, runtime dependencies, test configuration.
- `backend/app/main.py`: FastAPI app factory and router registration.
- `backend/app/core/config.py`: Settings object for paths, CORS, defaults, and portability knobs.
- `backend/app/core/paths.py`: Safe project path helpers and artifact path validation.
- `backend/app/db/session.py`: SQLite engine/session setup.
- `backend/app/db/models.py`: SQLAlchemy models for media, jobs, logs, frames, audio segments, embeddings.
- `backend/app/db/init_db.py`: Table creation helper.
- `backend/app/schemas/*.py`: Pydantic response/request schemas.
- `backend/app/encoders/base.py`: Encoder protocols and embedding result types.
- `backend/app/encoders/mock.py`: Deterministic mock image/audio encoders.
- `backend/app/storage/vector_store.py`: Vector store protocol and SQLite implementation.
- `backend/app/media/probe.py`: FFmpeg/ffprobe media metadata helpers.
- `backend/app/media/extract.py`: FFmpeg extraction helpers for frames/audio/segments.
- `backend/app/pipeline/jobs.py`: Job orchestration, logging, progress, and one-at-a-time lock.
- `backend/app/api/routes.py`: Health, upload, job, media, stats, and safe file APIs.
- `backend/tests/*`: Tests for settings/paths, DB, encoders, vector store, API smoke behavior.

Frontend files:

- `frontend/package.json`: Next.js project dependencies and scripts.
- `frontend/app/page.tsx`: Single workbench page.
- `frontend/app/layout.tsx`: Root layout.
- `frontend/app/globals.css`: Tailwind/shadcn styles.
- `frontend/lib/api.ts`: Backend API helper functions and types.
- `frontend/components/*`: Upload panel, job status, stats, frame grid, audio table, log panel, task list.
- `frontend/components/ui/*`: shadcn/ui primitives needed by the workbench.

Project files:

- `.gitignore`: Ignore environments, caches, generated data, and local worktrees.
- `environment.yml`: Conda environment for backend development.
- `README.md`: Local setup, FFmpeg install, run commands, portability notes.
- `data/.gitkeep`, `data/uploads/.gitkeep`, `data/extracted/.gitkeep`, `data/sqlite/.gitkeep`: Keep expected runtime directories.

## Task 1: Project Hygiene And Runtime Configuration

**Files:**
- Create: `.gitignore`
- Create: `environment.yml`
- Create: `README.md`
- Create: `data/.gitkeep`
- Create: `data/uploads/.gitkeep`
- Create: `data/extracted/.gitkeep`
- Create: `data/sqlite/.gitkeep`
- Create: `backend/pyproject.toml`

- [ ] **Step 1: Add project ignore rules**
  - Ignore Python caches, Node modules, build outputs, local `.env` files, generated runtime data under `data/`, and `.worktrees/`.
  - Keep `data/**/.gitkeep` tracked.

- [ ] **Step 2: Add conda environment file**
  - Define environment name `av-tokenvault`.
  - Use Python `3.11`.
  - Include pip dependencies for FastAPI, SQLAlchemy, pydantic-settings, uvicorn, python-multipart, pytest, httpx, and Pillow.

- [ ] **Step 3: Add backend project metadata**
  - Add `backend/pyproject.toml` with package name, pytest config, and runtime dependencies matching `environment.yml`.

- [ ] **Step 4: Add README setup skeleton**
  - Document `brew install ffmpeg`.
  - Document `conda env create -f environment.yml`.
  - Document backend and frontend start commands.
  - Explain that mock encoders are default and real models are later adapters.

- [ ] **Step 5: Commit**
  - Run: `git status --short`
  - Commit message: `chore: add project runtime skeleton`

## Task 2: Backend Config, Paths, And Database Models

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/core/paths.py`
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/db/models.py`
- Create: `backend/app/db/init_db.py`
- Create: `backend/tests/test_config_paths.py`
- Create: `backend/tests/test_db_models.py`

- [ ] **Step 1: Write failing path tests**
  - Test that default data directories resolve under the project root.
  - Test that `safe_artifact_path("../secret.txt")` is rejected.
  - Test that `safe_artifact_path("extracted/sample/frame.jpg")` resolves inside `data/`.

- [ ] **Step 2: Run tests and verify RED**
  - Run: `cd backend && pytest tests/test_config_paths.py -v`
  - Expected: fail because modules do not exist.

- [ ] **Step 3: Implement settings and safe paths**
  - Add `Settings` with project root, data root, upload root, extracted root, SQLite path, default intervals, max frames, and CORS origins.
  - Add `ensure_runtime_dirs()`.
  - Add `safe_artifact_path()` that normalizes paths and rejects path traversal outside `data/`.

- [ ] **Step 4: Run path tests and verify GREEN**
  - Run: `cd backend && pytest tests/test_config_paths.py -v`
  - Expected: pass.

- [ ] **Step 5: Write failing database model tests**
  - Create a temporary SQLite database.
  - Create tables.
  - Insert one media asset, one job, one log, one frame, one audio segment, and one embedding.
  - Assert relationships and counts.

- [ ] **Step 6: Run tests and verify RED**
  - Run: `cd backend && pytest tests/test_db_models.py -v`
  - Expected: fail because DB modules/models are missing.

- [ ] **Step 7: Implement SQLAlchemy models and session helpers**
  - Implement tables from the spec.
  - Use string statuses/modality fields for MVP simplicity.
  - Store embedding vectors as JSON text.
  - Add `create_db_and_tables()`.

- [ ] **Step 8: Run DB tests and verify GREEN**
  - Run: `cd backend && pytest tests/test_config_paths.py tests/test_db_models.py -v`
  - Expected: pass.

- [ ] **Step 9: Commit**
  - Commit message: `feat: add backend config and database models`

## Task 3: Encoder And Vector Store Extension Points

**Files:**
- Create: `backend/app/encoders/__init__.py`
- Create: `backend/app/encoders/base.py`
- Create: `backend/app/encoders/mock.py`
- Create: `backend/app/storage/__init__.py`
- Create: `backend/app/storage/vector_store.py`
- Create: `backend/tests/test_encoders.py`
- Create: `backend/tests/test_vector_store.py`

- [ ] **Step 1: Write failing mock encoder tests**
  - Test image and audio mock encoders return deterministic vectors.
  - Test encoder result includes encoder name, modality, and dimension.

- [ ] **Step 2: Run encoder tests and verify RED**
  - Run: `cd backend && pytest tests/test_encoders.py -v`
  - Expected: fail because encoder modules are missing.

- [ ] **Step 3: Implement encoder protocols and mock encoders**
  - Define `EmbeddingResult`.
  - Define image/audio encoder protocols.
  - Implement deterministic vectors based on file path bytes/hash so repeated runs are stable.

- [ ] **Step 4: Run encoder tests and verify GREEN**
  - Run: `cd backend && pytest tests/test_encoders.py -v`
  - Expected: pass.

- [ ] **Step 5: Write failing SQLite vector store tests**
  - Insert image and audio embeddings through a vector store adapter.
  - Assert records are persisted in the `embeddings` table.

- [ ] **Step 6: Run vector store tests and verify RED**
  - Run: `cd backend && pytest tests/test_vector_store.py -v`
  - Expected: fail because vector store is missing.

- [ ] **Step 7: Implement `VectorStore` protocol and SQLite adapter**
  - Add `add_embedding()` with media/job/source metadata.
  - Keep interface independent of SQLite so Chroma/FAISS can replace it later.

- [ ] **Step 8: Run tests and verify GREEN**
  - Run: `cd backend && pytest tests/test_encoders.py tests/test_vector_store.py -v`
  - Expected: pass.

- [ ] **Step 9: Commit**
  - Commit message: `feat: add mock encoders and vector store interface`

## Task 4: Media Processing Utilities

**Files:**
- Create: `backend/app/media/__init__.py`
- Create: `backend/app/media/probe.py`
- Create: `backend/app/media/extract.py`
- Create: `backend/tests/test_media_commands.py`

- [ ] **Step 1: Write failing FFmpeg command construction tests**
  - Test video frame extraction command includes frame interval and max frame cap.
  - Test audio extraction command outputs WAV.
  - Test audio segmentation command uses segment duration.
  - Tests should not require FFmpeg execution.

- [ ] **Step 2: Run tests and verify RED**
  - Run: `cd backend && pytest tests/test_media_commands.py -v`
  - Expected: fail because media modules are missing.

- [ ] **Step 3: Implement probe and extraction helpers**
  - Add `is_ffmpeg_available()`.
  - Add `probe_media()` using `ffprobe` JSON output.
  - Add command builder functions.
  - Add execution wrappers that raise readable errors on missing FFmpeg or command failure.

- [ ] **Step 4: Run tests and verify GREEN**
  - Run: `cd backend && pytest tests/test_media_commands.py -v`
  - Expected: pass without requiring FFmpeg installed.

- [ ] **Step 5: Commit**
  - Commit message: `feat: add ffmpeg media helpers`

## Task 5: Job Pipeline And Backend API

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/media.py`
- Create: `backend/app/pipeline/__init__.py`
- Create: `backend/app/pipeline/jobs.py`
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/routes.py`
- Create: `backend/app/main.py`
- Create: `backend/tests/test_api_smoke.py`
- Create: `backend/tests/test_job_pipeline.py`

- [ ] **Step 1: Write failing API smoke tests**
  - Test `GET /health`.
  - Test upload rejects unsupported extensions.
  - Test upload of a small fake `.wav` file creates media and pending job records.
  - Test stats endpoint returns zero counts for an unprocessed upload.

- [ ] **Step 2: Run API tests and verify RED**
  - Run: `cd backend && pytest tests/test_api_smoke.py -v`
  - Expected: fail because app/routes are missing.

- [ ] **Step 3: Implement FastAPI app and upload/read APIs**
  - Add app factory.
  - Add CORS for local frontend.
  - Add upload endpoint.
  - Add jobs, media, logs, frames, audio segments, stats endpoints.
  - Add safe file serving endpoint.

- [ ] **Step 4: Run API tests and verify GREEN**
  - Run: `cd backend && pytest tests/test_api_smoke.py -v`
  - Expected: pass.

- [ ] **Step 5: Write failing pipeline tests**
  - Use monkeypatch/fake extractors to avoid FFmpeg.
  - Assert a job transitions `pending -> running -> completed`.
  - Assert logs are persisted.
  - Assert mock embeddings are created for fake frames and audio segments.

- [ ] **Step 6: Run pipeline tests and verify RED**
  - Run: `cd backend && pytest tests/test_job_pipeline.py -v`
  - Expected: fail because pipeline is missing.

- [ ] **Step 7: Implement job pipeline**
  - Add one-at-a-time processing lock.
  - Add job logging helper.
  - Add progress updates.
  - Add media-type branches for video and audio.
  - Use extraction helpers and mock encoders.
  - Persist frames, audio segments, and embeddings through the vector store.

- [ ] **Step 8: Wire `POST /api/jobs/{job_id}/start`**
  - Start processing through FastAPI background tasks.
  - Return the current job response immediately.

- [ ] **Step 9: Run backend tests and verify GREEN**
  - Run: `cd backend && pytest -v`
  - Expected: pass.

- [ ] **Step 10: Commit**
  - Commit message: `feat: add media job pipeline and api`

## Task 6: Next.js Workbench UI

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/next.config.mjs`
- Create: `frontend/tsconfig.json`
- Create: `frontend/postcss.config.mjs`
- Create: `frontend/tailwind.config.ts`
- Create: `frontend/app/layout.tsx`
- Create: `frontend/app/page.tsx`
- Create: `frontend/app/globals.css`
- Create: `frontend/lib/api.ts`
- Create: `frontend/components/upload-panel.tsx`
- Create: `frontend/components/job-status.tsx`
- Create: `frontend/components/stats-panel.tsx`
- Create: `frontend/components/frame-grid.tsx`
- Create: `frontend/components/audio-segment-table.tsx`
- Create: `frontend/components/log-panel.tsx`
- Create: `frontend/components/task-list.tsx`
- Create: `frontend/components/ui/button.tsx`
- Create: `frontend/components/ui/card.tsx`
- Create: `frontend/components/ui/input.tsx`
- Create: `frontend/components/ui/label.tsx`
- Create: `frontend/components/ui/progress.tsx`
- Create: `frontend/components/ui/select.tsx`
- Create: `frontend/components/ui/table.tsx`
- Create: `frontend/components/ui/textarea.tsx`

- [ ] **Step 1: Scaffold minimal Next.js app files**
  - Use App Router.
  - Add local API base URL config through `NEXT_PUBLIC_API_BASE_URL`.

- [ ] **Step 2: Add API helper module**
  - Add typed functions for upload, start job, list jobs, fetch job, logs, frames, audio segments, stats.
  - Keep helpers isolated so frontend remains portable if backend host changes.

- [ ] **Step 3: Build workbench components**
  - Implement upload panel with parameters.
  - Implement job list and job status/progress.
  - Implement stats cards.
  - Implement frame grid using backend file URLs.
  - Implement audio segment table.
  - Implement log panel.

- [ ] **Step 4: Compose the single workbench page**
  - Keep UI simple and functional.
  - Poll active jobs every two seconds.
  - Refresh selected media result sections after job completion.

- [ ] **Step 5: Run frontend verification**
  - Run: `cd frontend && npm install`
  - Run: `cd frontend && npm run lint`
  - Run: `cd frontend && npm run build`
  - Expected: pass.

- [ ] **Step 6: Commit**
  - Commit message: `feat: add nextjs workbench ui`

## Task 7: Integration Verification And Documentation

**Files:**
- Modify: `README.md`
- Modify: `docs/superpowers/specs/2026-06-18-av-tokenvault-mvp-design.md`
- Create: `scripts/dev-backend.sh`
- Create: `scripts/dev-frontend.sh`

- [ ] **Step 1: Run backend verification**
  - Run: `cd backend && pytest -v`
  - Expected: pass.

- [ ] **Step 2: Run frontend verification**
  - Run: `cd frontend && npm run lint && npm run build`
  - Expected: pass.

- [ ] **Step 3: Check runtime dependencies**
  - Run: `ffmpeg -version`
  - If missing, document `brew install ffmpeg` and mark media execution smoke test as not run.

- [ ] **Step 4: Start backend and smoke health endpoint**
  - Run backend dev server.
  - Verify `GET /health` returns OK.

- [ ] **Step 5: Start frontend**
  - Run frontend dev server.
  - Verify local URL opens and renders workbench.

- [ ] **Step 6: Update README**
  - Include exact local setup commands.
  - Include Mac/conda notes.
  - Include portability notes for moving to a Linux/4090 machine.
  - Include extension notes for real encoders and vector stores.

- [ ] **Step 7: Commit**
  - Commit message: `docs: add local run and portability notes`
