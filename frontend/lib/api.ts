export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type MediaAsset = {
  id: number;
  filename: string;
  original_path: string;
  media_type: string;
  mime_type: string | null;
  duration_seconds: number | null;
  file_size: number;
  created_at: string;
};

export type ProcessingJob = {
  id: number;
  media_id: number;
  status: "pending" | "running" | "completed" | "failed" | string;
  progress: number;
  mode: string;
  frame_interval: number;
  segment_seconds: number;
  image_encoder: string;
  audio_encoder: string;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
};

export type UploadResponse = {
  media: MediaAsset;
  job: ProcessingJob;
};

export type JobLog = {
  id: number;
  job_id: number;
  level: string;
  message: string;
  created_at: string;
};

export type VideoFrame = {
  id: number;
  media_id: number;
  job_id: number;
  frame_index: number;
  timestamp_seconds: number;
  image_path: string;
  width: number | null;
  height: number | null;
};

export type AudioSegment = {
  id: number;
  media_id: number;
  job_id: number;
  segment_index: number;
  start_seconds: number;
  end_seconds: number;
  audio_path: string;
  duration_seconds: number;
};

export type MediaStats = {
  media_id: number;
  frame_count: number;
  audio_segment_count: number;
  embedding_count: number;
};

export type UploadParams = {
  file: File;
  frameInterval: number;
  segmentSeconds: number;
  imageEncoder: string;
  audioEncoder: string;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.headers ?? {})
    }
  });
  if (!response.ok) {
    let message = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      message = payload.detail ?? message;
    } catch {
      // Keep the HTTP status fallback.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export async function uploadMedia(params: UploadParams): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", params.file);
  formData.append("frame_interval", String(params.frameInterval));
  formData.append("segment_seconds", String(params.segmentSeconds));
  formData.append("image_encoder", params.imageEncoder);
  formData.append("audio_encoder", params.audioEncoder);
  return request<UploadResponse>("/api/media/upload", {
    method: "POST",
    body: formData
  });
}

export function startJob(jobId: number): Promise<ProcessingJob> {
  return request<ProcessingJob>(`/api/jobs/${jobId}/start`, { method: "POST" });
}

export function listJobs(): Promise<ProcessingJob[]> {
  return request<ProcessingJob[]>("/api/jobs");
}

export function getJob(jobId: number): Promise<ProcessingJob> {
  return request<ProcessingJob>(`/api/jobs/${jobId}`);
}

export function getJobLogs(jobId: number): Promise<JobLog[]> {
  return request<JobLog[]>(`/api/jobs/${jobId}/logs`);
}

export function getFrames(mediaId: number): Promise<VideoFrame[]> {
  return request<VideoFrame[]>(`/api/media/${mediaId}/frames`);
}

export function getAudioSegments(mediaId: number): Promise<AudioSegment[]> {
  return request<AudioSegment[]>(`/api/media/${mediaId}/audio-segments`);
}

export function getStats(mediaId: number): Promise<MediaStats> {
  return request<MediaStats>(`/api/media/${mediaId}/stats`);
}

export function artifactUrl(path: string): string {
  return `${API_BASE_URL}/api/files/${encodeURI(path)}`;
}
