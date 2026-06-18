import type { JobLog } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function LogPanel({ logs }: { logs: JobLog[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>处理日志</CardTitle>
      </CardHeader>
      <CardContent>
        {logs.length === 0 ? (
          <div className="text-sm text-muted-foreground">暂无日志</div>
        ) : (
          <div className="max-h-64 space-y-2 overflow-auto font-mono text-xs">
            {logs.map((log) => (
              <div key={log.id} className="rounded-md bg-muted px-3 py-2">
                <span className={log.level === "error" ? "text-destructive" : "text-muted-foreground"}>
                  [{log.level}]
                </span>{" "}
                {log.message}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
