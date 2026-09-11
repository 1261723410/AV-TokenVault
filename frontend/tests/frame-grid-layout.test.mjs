import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const frameGridSource = readFileSync(new URL("../components/frame-grid.tsx", import.meta.url), "utf8");

test("video frame preview keeps many frames in a scrollable region", () => {
  assert.match(frameGridSource, /max-h-\[/);
  assert.match(frameGridSource, /overflow-auto/);
  assert.match(frameGridSource, /pr-2/);
});
