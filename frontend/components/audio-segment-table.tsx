import type { AudioSegment } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export function AudioSegmentTable({ segments }: { segments: AudioSegment[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>音频片段</CardTitle>
      </CardHeader>
      <CardContent>
        {segments.length === 0 ? (
          <div className="text-sm text-muted-foreground">暂无音频片段</div>
        ) : (
          <div className="max-h-72 overflow-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>序号</TableHead>
                  <TableHead>开始</TableHead>
                  <TableHead>结束</TableHead>
                  <TableHead>路径</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {segments.map((segment) => (
                  <TableRow key={segment.id}>
                    <TableCell>{segment.segment_index}</TableCell>
                    <TableCell>{segment.start_seconds.toFixed(1)}s</TableCell>
                    <TableCell>{segment.end_seconds.toFixed(1)}s</TableCell>
                    <TableCell className="max-w-72 truncate font-mono text-xs">{segment.audio_path}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
