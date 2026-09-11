import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const pageSource = readFileSync(new URL("../app/page.tsx", import.meta.url), "utf8");
const searchPanelSource = readFileSync(new URL("../components/search-panel.tsx", import.meta.url), "utf8");

test("global search is positioned as a workspace toolbar before task details", () => {
  const searchIndex = pageSource.indexOf("<SearchPanel");
  const jobStatusIndex = pageSource.indexOf("<JobStatus");

  assert.notEqual(searchIndex, -1, "page should render SearchPanel");
  assert.notEqual(jobStatusIndex, -1, "page should render JobStatus");
  assert.ok(searchIndex < jobStatusIndex, "SearchPanel should appear before task-specific status panels");
});

test("search panel copy makes the all-library scope explicit", () => {
  assert.match(searchPanelSource, /全库语义检索/);
  assert.match(searchPanelSource, /全部已入库/);
  assert.match(searchPanelSource, /不局限于当前任务/);
});
