import type { MediaStats } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function StatsPanel({ stats }: { stats: MediaStats | null }) {
  const items = [
    ["视频帧", stats?.frame_count ?? 0],
    ["音频片段", stats?.audio_segment_count ?? 0],
    ["Embedding", stats?.embedding_count ?? 0]
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>入库统计</CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-3 gap-3">
        {items.map(([label, value]) => (
          <div key={label} className="rounded-md border bg-muted/40 p-3">
            <div className="text-xs text-muted-foreground">{label}</div>
            <div className="mt-1 text-2xl font-semibold">{value}</div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
