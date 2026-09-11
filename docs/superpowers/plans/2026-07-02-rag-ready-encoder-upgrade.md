# RAG-Ready Encoder Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade AV-TokenVault from mock-only embeddings to a real, optional, RAG-ready audio/video indexing pipeline while preserving the current local MVP and teacher-facing "tokenize and store" objective.

**Architecture:** Keep the current upload, extraction, job, SQLite, and UI flow intact. Add model adapters behind the existing encoder interfaces, persist derived text artifacts such as transcripts/captions separately from raw embeddings, and add a small retrieval API that proves the stored tokens/embeddings are useful without turning the project into a full RAG application. The first real path should be Whisper for speech-to-text plus BGE-M3 for text embeddings; CLIP/SigLIP and CLAP are planned as optional second-stage visual/audio semantic encoders.

**Tech Stack:** Python 3.11, FastAPI, SQLAlchemy, SQLite, FFmpeg, pytest, optional PyTorch/Transformers/SentenceTransformers/faster-whisper, Next.js, TypeScript, Tailwind, shadcn/ui-style components.

---

## Scope And Positioning

This plan intentionally does not build a complete RAG chatbot. It builds the data foundation that is "RAG-ready":

- Current teacher requirement remains primary: accept video/audio, extract frames/audio, tokenize/encode, and store results locally.
- RAG-readiness means the system can additionally produce searchable text artifacts with timestamps and retrieve relevant media segments.
- Heavy models are optional and configurable. The mock pipeline must continue to work on a Mac without GPU.
- Implementation should be incremental so every task leaves the app runnable.

## Recommended Model Roadmap

Phase 1 real model path:

- `whisper-*`: transcribe speech from audio segments into timestamped text.
- `bge-m3` or another local text embedding model: embed transcripts and later image captions.

Phase 2 visual path:

- `clip` or `siglip`: embed video frames for text-to-frame retrieval.
- Optional VLM captioner later, such as Qwen2.5-VL, to turn frames into searchable text.

Phase 3 generic audio path:

- `clap`: embed non-speech audio events for text-to-audio retrieval.

## File Map

Backend files to modify:

- `environment.yml`: add optional model dependencies only when the user approves installing them.
- `backend/pyproject.toml`: mirror optional dependency groups.
- `backend/app/core/config.py`: add model provider settings, device settings, cache paths, and feature flags.
- `backend/app/db/models.py`: add tables or columns for transcript/caption/search artifacts.
- `backend/app/schemas/media.py`: add response schemas for transcript and search results.
- `backend/app/encoders/base.py`: extend encoder protocols to cover text embedding and transcript generation without breaking existing mock encoders.
- `backend/app/encoders/mock.py`: add mock transcriber/text embedder for tests and no-model fallback.
- `backend/app/encoders/registry.py`: new model registry that resolves selected encoder names to adapters.
- `backend/app/encoders/whisper.py`: new optional Whisper adapter.
- `backend/app/encoders/text_embedding.py`: new optional BGE/text embedding adapter.
- `backend/app/encoders/clip.py`: optional later visual encoder adapter.
- `backend/app/encoders/clap.py`: optional later audio-event adapter.
- `backend/app/storage/vector_store.py`: add similarity search helpers for SQLite-backed vectors.
- `backend/app/pipeline/jobs.py`: orchestrate transcription, text embedding, and optional frame/audio semantic embeddings.
- `backend/app/api/routes.py`: expose transcript and search endpoints.

Backend test files:

- `backend/tests/test_encoder_registry.py`: registry behavior and fallback.
- `backend/tests/test_transcripts.py`: DB persistence for transcript chunks.
- `backend/tests/test_text_embeddings.py`: mock text embedding behavior and vector store search.
- `backend/tests/test_search_api.py`: API-level retrieval smoke tests.
- `backend/tests/test_job_pipeline.py`: pipeline regression tests for transcript + embedding creation.

Frontend files to modify:

- `frontend/lib/api.ts`: add transcript/search API types and functions.
- `frontend/app/page.tsx`: wire transcript/search panels into the workbench.
- `frontend/components/upload-panel.tsx`: expose model choices without overwhelming the UI.
- `frontend/components/job-status.tsx`: show selected models and processing status.
- `frontend/components/transcript-panel.tsx`: new panel for timestamped transcript chunks.
- `frontend/components/search-panel.tsx`: new simple query input and result list.
- `frontend/components/stats-panel.tsx`: show transcript/caption/searchable artifact counts.

Docs files:

- `README.md`: explain mock vs real model modes and Mac/GPU notes.
- `docs/model-selection-notes.md`: short teacher-facing explanation of encoder choices.

## Task 1: Add Data Model For RAG-Ready Artifacts

**Files:**
- Modify: `backend/app/db/models.py`
- Modify: `backend/app/schemas/media.py`
- Modify: `backend/app/api/routes.py`
- Create: `backend/tests/test_transcripts.py`

- [ ] **Step 1: Write failing DB test for transcript chunks**

  Test that a media/job can store ordered transcript chunks with timestamps:

  ```python
  def test_transcript_chunks_belong_to_media_and_job(session):
      chunk = TranscriptChunk(
          media_id=media.id,
          job_id=job.id,
          audio_segment_id=segment.id,
          chunk_index=0,
          start_seconds=0.0,
          end_seconds=5.0,
          text="老师讲到音视频 token 化。",
          language="zh",
          source="mock-transcriber",
      )
      session.add(chunk)
      session.commit()
      assert session.query(TranscriptChunk).count() == 1
  ```

- [ ] **Step 2: Run test and verify RED**

  Run: `conda run -n av-tokenvault pytest backend/tests/test_transcripts.py -v`

  Expected: fail because `TranscriptChunk` does not exist.

- [ ] **Step 3: Add `TranscriptChunk` model**

  Add table `transcript_chunks` with:

  - `id`
  - `media_id`
  - `job_id`
  - `audio_segment_id`
  - `chunk_index`
  - `start_seconds`
  - `end_seconds`
  - `text`
  - `language`
  - `source`
  - `created_at`

- [ ] **Step 4: Add schema and API read endpoint**

  Add `TranscriptChunkRead`.

  Add:

  ```text
  GET /api/media/{media_id}/transcripts
  ```

- [ ] **Step 5: Run focused tests**

  Run: `conda run -n av-tokenvault pytest backend/tests/test_transcripts.py backend/tests/test_api_smoke.py -v`

  Expected: pass.

- [ ] **Step 6: Commit**

  Commit message: `feat: add transcript artifact model`

## Task 2: Add Encoder Registry And Mock RAG-Ready Adapters

**Files:**
- Modify: `backend/app/encoders/base.py`
- Modify: `backend/app/encoders/mock.py`
- Create: `backend/app/encoders/registry.py`
- Create: `backend/tests/test_encoder_registry.py`
- Create: `backend/tests/test_text_embeddings.py`

- [ ] **Step 1: Write failing registry tests**

  Cover:

  - default `mock-image-encoder` still resolves.
  - default `mock-audio-encoder` still resolves.
  - new `mock-transcriber` resolves.
  - new `mock-text-embedder` resolves.
  - unknown names raise readable `ValueError`.

- [ ] **Step 2: Run registry test and verify RED**

  Run: `conda run -n av-tokenvault pytest backend/tests/test_encoder_registry.py -v`

  Expected: fail because registry does not exist.

- [ ] **Step 3: Add protocol types**

  Add:

  - `TranscriptResult`
  - `TranscriptChunkResult`
  - `Transcriber` protocol
  - `TextEmbeddingEncoder` protocol

  Keep existing `ImageEncoder`, `AudioEncoder`, and `EmbeddingResult`.

- [ ] **Step 4: Implement mock transcriber and mock text embedder**

  `MockTranscriber` returns deterministic text based on the segment path and timestamp.

  `MockTextEmbedder` returns deterministic 32-dimensional vectors, same style as current mock encoders.

- [ ] **Step 5: Implement registry**

  Add functions:

  - `get_image_encoder(name: str)`
  - `get_audio_encoder(name: str)`
  - `get_transcriber(name: str)`
  - `get_text_embedder(name: str)`

  Registry must import heavy optional adapters lazily so mock mode stays lightweight.

- [ ] **Step 6: Run tests**

  Run: `conda run -n av-tokenvault pytest backend/tests/test_encoder_registry.py backend/tests/test_encoders.py -v`

  Expected: pass.

- [ ] **Step 7: Commit**

  Commit message: `feat: add encoder registry and mock transcriber`

## Task 3: Extend Pipeline To Produce Transcript And Text Embeddings

**Files:**
- Modify: `backend/app/db/models.py`
- Modify: `backend/app/pipeline/jobs.py`
- Modify: `backend/app/storage/vector_store.py`
- Modify: `backend/tests/test_job_pipeline.py`
- Create: `backend/tests/test_text_embeddings.py`

- [ ] **Step 1: Write failing pipeline test**

  Use fake extraction and mock transcriber. Assert:

  - audio segments are created.
  - transcript chunks are created for each audio segment.
  - text embeddings are created with `modality="text"` and `source_type="transcript_chunk"`.
  - existing image/audio embedding behavior still works.

- [ ] **Step 2: Run test and verify RED**

  Run: `conda run -n av-tokenvault pytest backend/tests/test_job_pipeline.py::test_process_job_creates_transcript_text_embeddings -v`

  Expected: fail because pipeline does not create transcripts/text embeddings.

- [ ] **Step 3: Add job fields for model choices**

  Minimal option:

  - Add nullable `transcriber` and `text_encoder` fields to `processing_jobs`.
  - Keep existing jobs compatible by defaulting to mock choices in code when fields are null.

  If avoiding schema migration complexity for MVP, use existing `audio_encoder` only for audio embeddings and add defaults in settings before creating new jobs.

- [ ] **Step 4: Implement transcript creation**

  In `process_job()` after audio segments are written:

  - Resolve transcriber from registry.
  - Transcribe each segment.
  - Persist `TranscriptChunk` rows with media/job/segment metadata.

- [ ] **Step 5: Implement text embedding creation**

  - Resolve text embedder from registry.
  - Embed each transcript chunk.
  - Store embeddings with:

    ```text
    modality = "text"
    source_type = "transcript_chunk"
    source_id = transcript_chunk.id
    ```

- [ ] **Step 6: Run focused tests**

  Run: `conda run -n av-tokenvault pytest backend/tests/test_job_pipeline.py backend/tests/test_vector_store.py -v`

  Expected: pass.

- [ ] **Step 7: Commit**

  Commit message: `feat: create transcript text embeddings`

## Task 4: Add SQLite Similarity Search For Local Demo

**Files:**
- Modify: `backend/app/storage/vector_store.py`
- Modify: `backend/app/api/routes.py`
- Modify: `backend/app/schemas/media.py`
- Create: `backend/tests/test_search_api.py`

- [ ] **Step 1: Write failing vector search test**

  Insert a few embeddings with known vectors and assert cosine similarity ranking.

- [ ] **Step 2: Run test and verify RED**

  Run: `conda run -n av-tokenvault pytest backend/tests/test_text_embeddings.py::test_sqlite_vector_store_ranks_by_cosine_similarity -v`

  Expected: fail because search helper does not exist.

- [ ] **Step 3: Implement vector search helper**

  Add:

  ```python
  def search_embeddings(query_vector: list[float], *, modality: str | None, limit: int) -> list[SearchHit]:
  ```

  Keep it simple: load vectors from SQLite and rank in Python. This is acceptable for local prototype scale.

- [ ] **Step 4: Add search endpoint**

  Add:

  ```text
  POST /api/search
  ```

  Request:

  - `query`
  - `modality`: `text`, `image`, `audio`, or `all`
  - `limit`

  Initial implementation embeds query with the selected text embedder and searches text embeddings first.

- [ ] **Step 5: Run API tests**

  Run: `conda run -n av-tokenvault pytest backend/tests/test_search_api.py -v`

  Expected: pass.

- [ ] **Step 6: Commit**

  Commit message: `feat: add local embedding search api`

## Task 5: Add Real Whisper Adapter As Optional Model

**Files:**
- Modify: `environment.yml`
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/core/config.py`
- Create: `backend/app/encoders/whisper.py`
- Create: `backend/tests/test_encoder_registry.py`
- Create: `backend/tests/test_whisper_adapter.py`

- [ ] **Step 1: Decide dependency strategy before coding**

  Recommended Mac-friendly dependency:

  - `faster-whisper` for local CPU/MPS-friendly transcription where possible.

  Alternative:

  - OpenAI `whisper` package, simpler conceptually but often heavier/slower locally.

- [ ] **Step 2: Add dependency as optional**

  Prefer optional install instructions first. Do not make baseline tests require downloading a model.

- [ ] **Step 3: Write adapter import/fallback test**

  Test that registry gives a readable error if `faster-whisper` is unavailable.

- [ ] **Step 4: Implement adapter**

  Add `FasterWhisperTranscriber` with lazy model loading and configurable:

  - model size, default `base` or `small`
  - device, default `cpu`
  - compute type, default `int8`
  - model cache path

- [ ] **Step 5: Add manual smoke command**

  Document:

  ```bash
  conda run -n av-tokenvault python -m app.encoders.whisper data/extracted/job_9/segments/segment_000000.wav
  ```

- [ ] **Step 6: Run tests**

  Run: `conda run -n av-tokenvault pytest backend/tests/test_encoder_registry.py backend/tests/test_whisper_adapter.py -v`

  Expected: pass without requiring model download.

- [ ] **Step 7: Commit**

  Commit message: `feat: add optional whisper transcriber`

## Task 6: Add Real Text Embedding Adapter

**Files:**
- Modify: `environment.yml`
- Modify: `backend/pyproject.toml`
- Modify: `backend/app/core/config.py`
- Create: `backend/app/encoders/text_embedding.py`
- Modify: `backend/app/encoders/registry.py`
- Create: `backend/tests/test_text_embedding_adapter.py`

- [ ] **Step 1: Choose default model**

  Recommended:

  - `BAAI/bge-m3` for Chinese/multilingual RAG-ready retrieval.

  Lightweight fallback:

  - `BAAI/bge-small-zh-v1.5` if local Mac performance becomes painful.

- [ ] **Step 2: Add optional dependency**

  Add install notes for:

  - `sentence-transformers`
  - `torch`

  Avoid forcing these on the base MVP unless approved.

- [ ] **Step 3: Write adapter fallback test**

  If `sentence-transformers` is missing, registry should raise a readable setup message.

- [ ] **Step 4: Implement adapter**

  Add `SentenceTransformerTextEmbedder`.

  Normalize vectors before storing if the model does not already do so.

- [ ] **Step 5: Run tests**

  Run: `conda run -n av-tokenvault pytest backend/tests/test_text_embedding_adapter.py backend/tests/test_text_embeddings.py -v`

  Expected: pass without requiring model download in unit tests.

- [ ] **Step 6: Manual smoke test with small text**

  After installing optional dependency:

  ```bash
  conda run -n av-tokenvault python -m app.encoders.text_embedding "音视频 token 化"
  ```

- [ ] **Step 7: Commit**

  Commit message: `feat: add optional text embedding adapter`

## Task 7: Add Frontend Transcript And Search Panels

**Files:**
- Modify: `frontend/lib/api.ts`
- Modify: `frontend/app/page.tsx`
- Modify: `frontend/components/upload-panel.tsx`
- Create: `frontend/components/transcript-panel.tsx`
- Create: `frontend/components/search-panel.tsx`
- Modify: `frontend/components/stats-panel.tsx`

- [ ] **Step 1: Add TypeScript API types**

  Add:

  - `TranscriptChunk`
  - `SearchRequest`
  - `SearchResult`
  - `getTranscripts(mediaId)`
  - `searchMedia(payload)`

- [ ] **Step 2: Add transcript panel**

  Display:

  - timestamp range
  - transcript text
  - source model

  Keep UI simple and consistent with existing cards.

- [ ] **Step 3: Add search panel**

  Include:

  - text input
  - modality selector
  - result list with score, source type, media/job id, timestamp if available

- [ ] **Step 4: Wire page state**

  When selected job changes:

  - load stats
  - load frames
  - load audio segments
  - load transcripts
  - load logs

- [ ] **Step 5: Avoid the previous CSS cache issue during checks**

  If dev server is running, do not run `next build` against the same `.next` directory. Either stop the dev server first or only run `npm run lint` during live UI iteration.

- [ ] **Step 6: Run frontend checks**

  Run:

  ```bash
  cd frontend
  npm run lint
  ```

  For production build, first stop dev server or use a clean build process.

- [ ] **Step 7: Commit**

  Commit message: `feat: add transcript and search ui`

## Task 8: Optional Visual Encoder Path

**Files:**
- Create: `backend/app/encoders/clip.py`
- Modify: `backend/app/encoders/registry.py`
- Modify: `backend/app/pipeline/jobs.py`
- Modify: `frontend/components/upload-panel.tsx`
- Create: `backend/tests/test_clip_adapter.py`

- [ ] **Step 1: Decide CLIP vs SigLIP**

  Recommended first implementation:

  - OpenCLIP/CLIP if easiest to install locally.
  - SigLIP later if model quality matters more than installation simplicity.

- [ ] **Step 2: Add optional adapter**

  Keep lazy import and readable missing-dependency errors.

- [ ] **Step 3: Store frame embeddings with real encoder**

  Continue using existing `embeddings` table:

  - `modality="image"`
  - `source_type="frame"`

- [ ] **Step 4: Add text-to-frame search**

  Embed query in same image-text model space and return related frames.

- [ ] **Step 5: Manual demo**

  Query examples:

  - "有图表的画面"
  - "有人在讲话"
  - "实验设备"

- [ ] **Step 6: Commit**

  Commit message: `feat: add optional visual retrieval encoder`

## Task 9: Optional CLAP Audio Event Path

**Files:**
- Create: `backend/app/encoders/clap.py`
- Modify: `backend/app/encoders/registry.py`
- Modify: `backend/app/pipeline/jobs.py`
- Create: `backend/tests/test_clap_adapter.py`

- [ ] **Step 1: Confirm whether non-speech audio matters**

  Only implement if the target demo includes music, machine noise, alarms, applause, or environmental sound.

- [ ] **Step 2: Add optional CLAP adapter**

  Keep it out of the default processing path unless selected by user.

- [ ] **Step 3: Add audio-event search mode**

  Query examples:

  - "掌声"
  - "背景音乐"
  - "机器运行声"

- [ ] **Step 4: Commit**

  Commit message: `feat: add optional audio event encoder`

## Task 10: Documentation And Demo Script

**Files:**
- Modify: `README.md`
- Create: `docs/model-selection-notes.md`
- Create: `docs/demo-script.md`

- [ ] **Step 1: Update README**

  Explain three modes:

  - mock mode: default, no heavy dependencies
  - speech RAG-ready mode: Whisper + text embeddings
  - optional visual/audio semantic mode: CLIP/CLAP

- [ ] **Step 2: Write teacher-facing model notes**

  Include:

  - why current mock encoders exist
  - why Whisper/BGE-M3 are the first practical upgrade
  - why CLIP/SigLIP and CLAP are optional
  - why this is "RAG-ready" but not necessarily a full RAG app

- [ ] **Step 3: Write demo script**

  Demo should show:

  - upload video
  - start processing
  - inspect frames/audio segments
  - inspect transcript chunks
  - search a text query
  - open matched timestamp/frame

- [ ] **Step 4: Run full verification**

  Backend:

  ```bash
  conda run -n av-tokenvault pytest -q
  ```

  Frontend:

  ```bash
  cd frontend
  npm run lint
  ```

  Production build only after stopping dev server:

  ```bash
  cd frontend
  npm run build
  ```

- [ ] **Step 5: Commit**

  Commit message: `docs: explain rag-ready encoder upgrade`

## Suggested Implementation Order For This Project

Recommended for the next development round:

1. Task 1: transcript artifact model.
2. Task 2: encoder registry + mock transcriber/text embedder.
3. Task 3: pipeline creates transcript + text embeddings.
4. Task 4: local search API.
5. Task 7: frontend transcript/search panels.
6. Task 10: docs and demo script.

Only after this works should we consider real model dependencies:

7. Task 5: Whisper adapter.
8. Task 6: BGE-M3/text embedding adapter.
9. Task 8: CLIP/SigLIP visual retrieval.
10. Task 9: CLAP audio-event retrieval.

This order keeps the system demonstrable after each phase and avoids breaking the current local Mac MVP with heavy dependencies too early.

## Acceptance Criteria

- Existing mock workflow still works end to end.
- A video job still creates frame, audio segment, and embedding records.
- A video/audio job can also create transcript chunks and text embeddings in mock mode.
- Search API can return relevant stored transcript chunks in local SQLite mode.
- UI can show transcript chunks and search results.
- Real model adapters are optional and fail with readable setup messages when dependencies are not installed.
- README clearly explains that the project satisfies the teacher's tokenization/storage requirement and is prepared for retrieval/RAG applications.
- Backend tests pass.
- Frontend lint passes.
