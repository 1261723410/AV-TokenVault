"use client";

import type { ProcessingJob } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function TaskList({
  jobs,
  selectedJobId,
  onSelect
}: {
  jobs: ProcessingJob[];
  selectedJobId: number | null;
  onSelect: (job: ProcessingJob) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>最近任务</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {jobs.length === 0 ? (
          <div className="text-sm text-muted-foreground">暂无上传记录</div>
        ) : (
          jobs.map((job) => (
            <button
              key={job.id}
              className={cn(
                "w-full rounded-md border px-3 py-2 text-left text-sm transition-colors hover:bg-muted",
                selectedJobId === job.id && "border-primary bg-muted"
              )}
              onClick={() => onSelect(job)}
            >
              <div className="flex items-center justify-between gap-2">
                <span>任务 #{job.id}</span>
                <span className="text-xs text-muted-foreground">{job.status}</span>
              </div>
              <div className="mt-1 text-xs text-muted-foreground">媒体 ID：{job.media_id}</div>
            </button>
          ))
        )}
      </CardContent>
    </Card>
  );
}
