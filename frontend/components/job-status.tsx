"use client";

import { Play } from "lucide-react";
import type { ProcessingJob } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";

export function JobStatus({
  job,
  onStart,
  busy
}: {
  job: ProcessingJob | null;
  onStart: (jobId: number) => void;
  busy?: boolean;
}) {
  if (!job) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>任务状态</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">暂无任务</CardContent>
      </Card>
    );
  }

  const progress = Math.round(job.progress * 100);
  const canStart = job.status === "pending" || job.status === "failed";

  return (
    <Card>
      <CardHeader>
        <CardTitle>任务 #{job.id}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <div className="text-sm text-muted-foreground">状态</div>
            <div className="font-medium">{job.status}</div>
          </div>
          <Button size="sm" onClick={() => onStart(job.id)} disabled={!canStart || busy}>
            <Play className="h-4 w-4" />
            开始处理
          </Button>
        </div>
        <Progress value={progress} />
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-muted-foreground">抽帧：</span>
            {job.frame_interval}s
          </div>
          <div>
            <span className="text-muted-foreground">切片：</span>
            {job.segment_seconds}s
          </div>
          <div className="col-span-2">
            <span className="text-muted-foreground">图像模型：</span>
            {job.image_encoder}
          </div>
          <div className="col-span-2">
            <span className="text-muted-foreground">音频模型：</span>
            {job.audio_encoder}
          </div>
        </div>
        {job.error_message ? <div className="text-sm text-destructive">{job.error_message}</div> : null}
      </CardContent>
    </Card>
  );
}
