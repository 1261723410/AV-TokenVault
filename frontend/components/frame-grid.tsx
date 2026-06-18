import type { VideoFrame } from "@/lib/api";
import { artifactUrl } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function FrameGrid({ frames }: { frames: VideoFrame[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>视频帧预览</CardTitle>
      </CardHeader>
      <CardContent>
        {frames.length === 0 ? (
          <div className="text-sm text-muted-foreground">暂无视频帧</div>
        ) : (
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {frames.map((frame) => (
              <figure key={frame.id} className="overflow-hidden rounded-md border bg-muted/30">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={artifactUrl(frame.image_path)}
                  alt={`frame ${frame.frame_index}`}
                  className="aspect-video w-full object-cover"
                />
                <figcaption className="px-2 py-1 text-xs text-muted-foreground">
                  #{frame.frame_index} · {frame.timestamp_seconds.toFixed(1)}s
                </figcaption>
              </figure>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
