"use client";

import { Database, Search } from "lucide-react";
import { useState } from "react";
import type { SearchResult } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function confidenceLabel(score: number): string {
  if (score >= 0.35) {
    return "较高置信度";
  }
  if (score >= 0.22) {
    return "中等置信度";
  }
  return "低置信度";
}

function evidenceText(result: SearchResult): string {
  if (result.source_type === "transcript_chunk") {
    return "匹配依据：文本向量相似度；这是查询文本和会议转写片段的匹配。";
  }
  return "匹配依据：向量相似度。";
}

export function SearchPanel({
  busy,
  results,
  onSearch
}: {
  busy?: boolean;
  results: SearchResult[];
  onSearch: (query: string, modality: string) => void;
}) {
  const [hasSearched, setHasSearched] = useState(false);

  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const query = String(form.get("query") ?? "").trim();
    if (!query) {
      return;
    }
    setHasSearched(true);
    onSearch(query, "text");
  }

  return (
    <Card className="border-primary/20">
      <CardHeader className="pb-3">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="space-y-1">
            <CardTitle>全库语义检索</CardTitle>
            <p className="text-sm text-muted-foreground">
              搜索全部已入库的转写片段和向量结果，不局限于当前任务。
            </p>
          </div>
          <span className="inline-flex w-fit items-center gap-1 rounded-md border bg-muted/40 px-2 py-1 text-xs font-medium text-muted-foreground">
            <Database className="h-3.5 w-3.5" />
            全部媒体
          </span>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <form className="grid gap-3 md:grid-cols-[minmax(0,1fr)_auto]" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="query">查询内容</Label>
            <Input id="query" name="query" placeholder="例如：会议摘要、bye bye、某个场景描述" />
          </div>
          <div className="flex items-end">
            <Button className="w-full md:w-auto" type="submit" disabled={busy}>
              <Search className="h-4 w-4" />
              检索
            </Button>
          </div>
        </form>

        {results.length === 0 ? (
          <div className="rounded-md border border-dashed bg-muted/20 px-3 py-2 text-sm text-muted-foreground">
            {hasSearched ? "没有匹配结果" : "输入关键词后，会在全部已入库媒体中检索。"}
          </div>
        ) : (
          <div className="max-h-72 space-y-3 overflow-auto">
            {results.map((result) => (
              <div key={result.embedding_id} className="rounded-md border bg-muted/30 p-3">
                <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                  <span>媒体 #{result.media_id}</span>
                  <span>任务 #{result.job_id}</span>
                  <span>{result.source_type}</span>
                  <span>score {result.score.toFixed(3)}</span>
                  <span>{confidenceLabel(result.score)}</span>
                  {result.start_seconds !== null && result.end_seconds !== null ? (
                    <span>
                      {result.start_seconds.toFixed(1)}s - {result.end_seconds.toFixed(1)}s
                    </span>
                  ) : null}
                </div>
                <div className="mt-2 rounded-md border border-dashed bg-background/70 px-2 py-1.5 text-xs leading-5 text-muted-foreground">
                  {evidenceText(result)}
                </div>
                {result.text ? <p className="mt-2 text-sm leading-6">{result.text}</p> : null}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
