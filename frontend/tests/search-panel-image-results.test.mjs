import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const apiSource = readFileSync(new URL("../lib/api.ts", import.meta.url), "utf8");
const searchPanelSource = readFileSync(new URL("../components/search-panel.tsx", import.meta.url), "utf8");

test("search API type no longer exposes frame result metadata", () => {
  assert.doesNotMatch(apiSource, /image_path: string \| null/);
  assert.doesNotMatch(apiSource, /timestamp_seconds: number \| null/);
});

test("search panel no longer exposes video frame search", () => {
  assert.doesNotMatch(searchPanelSource, /视频画面/);
  assert.doesNotMatch(searchPanelSource, /OpenCLIP 视觉语义/);
  assert.doesNotMatch(searchPanelSource, /artifactUrl\(result\.image_path\)/);
});

test("search panel submits text search explicitly", () => {
  assert.match(searchPanelSource, /onSearch\(query, "text"\)/);
});
