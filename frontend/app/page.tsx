"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AudioSegmentTable } from "@/components/audio-segment-table";
import { FrameGrid } from "@/components/frame-grid";
import { JobStatus } from "@/components/job-status";
import { LogPanel } from "@/components/log-panel";
import { SearchPanel } from "@/components/search-panel";
import { StatsPanel } from "@/components/stats-panel";
import { TaskList } from "@/components/task-list";
import { TranscriptPanel } from "@/components/transcript-panel";
import { UploadPanel } from "@/components/upload-panel";
import {
  type AudioSegment,
  type JobLog,
  type MediaStats,
  type ProcessingJob,
  type SearchResult,
  type TranscriptChunk,
  type UploadParams,
  type VideoFrame,
  API_BASE_URL,
  getAudioSegments,
  getFrames,
  getJob,
  getJobLogs,
  getStats,
  getTranscripts,
  listJobs,
  searchMedia,
  startJob,
  uploadMedia
} from "@/lib/api";

export default function Home() {
  const [jobs, setJobs] = useState<ProcessingJob[]>([]);
  const [selectedJob, setSelectedJob] = useState<ProcessingJob | null>(null);
  const [stats, setStats] = useState<MediaStats | null>(null);
  const [frames, setFrames] = useState<VideoFrame[]>([]);
  const [segments, setSegments] = useState<AudioSegment[]>([]);
  const [transcripts, setTranscripts] = useState<TranscriptChunk[]>([]);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [logs, setLogs] = useState<JobLog[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeJob = useMemo(() => selectedJob, [selectedJob]);

  const refreshJobs = useCallback(async () => {
    const nextJobs = await listJobs();
    setJobs(nextJobs);
    setSelectedJob((current) => {
      if (!current) {
        return nextJobs[0] ?? null;
      }
      return nextJobs.find((job) => job.id === current.id) ?? current;
    });
  }, []);

  const refreshResults = useCallback(async (job: ProcessingJob | null) => {
    if (!job) {
      setStats(null);
      setFrames([]);
      setSegments([]);
      setTranscripts([]);
      setLogs([]);
      return;
    }
    const [nextStats, nextFrames, nextSegments, nextTranscripts, nextLogs] = await Promise.all([
      getStats(job.media_id),
      getFrames(job.media_id),
      getAudioSegments(job.media_id),
      getTranscripts(job.media_id),
      getJobLogs(job.id)
    ]);
    setStats(nextStats);
    setFrames(nextFrames);
    setSegments(nextSegments);
    setTranscripts(nextTranscripts);
    setLogs(nextLogs);
  }, []);

  useEffect(() => {
    refreshJobs().catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  }, [refreshJobs]);

  useEffect(() => {
    refreshResults(activeJob).catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)));
  }, [activeJob, refreshResults]);

  useEffect(() => {
    if (!activeJob || activeJob.status !== "running") {
      return;
    }
    const timer = window.setInterval(async () => {
      try {
        const job = await getJob(activeJob.id);
        setSelectedJob(job);
        await refreshJobs();
        await refreshResults(job);
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err));
      }
    }, 2000);
    return () => window.clearInterval(timer);
  }, [activeJob, refreshJobs, refreshResults]);

  async function handleUpload(params: UploadParams) {
    setBusy(true);
    setError(null);
    try {
      const response = await uploadMedia(params);
      setSelectedJob(response.job);
      await refreshJobs();
      await refreshResults(response.job);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleStart(jobId: number) {
    setBusy(true);
    setError(null);
    try {
      const job = await startJob(jobId);
      setSelectedJob(job);
      await refreshJobs();
      await refreshResults(job);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleSearch(query: string, modality: string) {
    setBusy(true);
    setError(null);
    try {
      const response = await searchMedia(query, modality, 5);
      setSearchResults(response.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="min-h-screen bg-muted/30">
      <div className="mx-auto flex max-w-7xl flex-col gap-5 px-4 py-6">
        <header className="flex flex-col gap-1">
          <h1 className="text-2xl font-semibold tracking-normal">音视频令牌化向量存储系统软件 V1.0</h1>
          <p className="text-sm text-muted-foreground">本地音视频令牌化、向量入库与检索工作台</p>
        </header>

        {error ? (
          <div className="rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
            <div className="mt-1 text-xs text-destructive/80">API：{API_BASE_URL}</div>
          </div>
        ) : null}

        <div className="grid gap-5 lg:grid-cols-[340px_1fr]">
          <aside className="space-y-5">
            <UploadPanel disabled={busy} onUpload={handleUpload} />
            <TaskList jobs={jobs} selectedJobId={selectedJob?.id ?? null} onSelect={setSelectedJob} />
          </aside>

          <section className="space-y-5">
            <SearchPanel busy={busy} results={searchResults} onSearch={handleSearch} />
            <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
              <JobStatus job={selectedJob} onStart={handleStart} busy={busy} />
              <StatsPanel stats={stats} />
            </div>
            <FrameGrid frames={frames} />
            <AudioSegmentTable segments={segments} />
            <TranscriptPanel chunks={transcripts} />
            <LogPanel logs={logs} />
          </section>
        </div>
      </div>
    </main>
  );
}
