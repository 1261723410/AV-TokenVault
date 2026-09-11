import type { TranscriptChunk } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function TranscriptPanel({ chunks }: { chunks: TranscriptChunk[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>转写片段</CardTitle>
      </CardHeader>
      <CardContent>
        {chunks.length === 0 ? (
          <div className="text-sm text-muted-foreground">暂无转写片段</div>
        ) : (
          <div className="max-h-80 space-y-3 overflow-auto">
            {chunks.map((chunk) => (
              <div key={chunk.id} className="rounded-md border bg-muted/30 p-3">
                <div className="mb-1 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <span>
                    {chunk.start_seconds.toFixed(1)}s - {chunk.end_seconds.toFixed(1)}s
                  </span>
                  <span>{chunk.source}</span>
                </div>
                <p className="text-sm leading-6">{chunk.text}</p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
