"use client";

import { Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";

type UploadPanelProps = {
  disabled?: boolean;
  onUpload: (payload: {
    file: File;
    frameInterval: number;
    segmentSeconds: number;
    imageEncoder: string;
    audioEncoder: string;
  }) => void;
};

export function UploadPanel({ disabled, onUpload }: UploadPanelProps) {
  function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const file = form.get("file");
    if (!(file instanceof File) || file.size === 0) {
      return;
    }
    onUpload({
      file,
      frameInterval: Number(form.get("frameInterval") ?? 2),
      segmentSeconds: Number(form.get("segmentSeconds") ?? 5),
      imageEncoder: String(form.get("imageEncoder") ?? "mock-image-encoder"),
      audioEncoder: String(form.get("audioEncoder") ?? "mock-audio-encoder")
    });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>上传与处理参数</CardTitle>
      </CardHeader>
      <CardContent>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <div className="space-y-2">
            <Label htmlFor="file">音视频文件</Label>
            <Input id="file" name="file" type="file" accept=".mp4,.mov,.wav,.mp3" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-2">
              <Label htmlFor="frameInterval">抽帧间隔（秒）</Label>
              <Input id="frameInterval" name="frameInterval" type="number" min="0.5" step="0.5" defaultValue="2" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="segmentSeconds">音频切片（秒）</Label>
              <Input id="segmentSeconds" name="segmentSeconds" type="number" min="1" step="1" defaultValue="5" />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="imageEncoder">图像 encoder</Label>
            <Select id="imageEncoder" name="imageEncoder" defaultValue="mock-image-encoder">
              <option value="mock-image-encoder">mock-image-encoder</option>
              <option value="open-clip:ViT-B-32:laion2b_s34b_b79k">OpenCLIP ViT-B-32</option>
            </Select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="audioEncoder">音频 encoder</Label>
            <Select id="audioEncoder" name="audioEncoder" defaultValue="mock-audio-encoder">
              <option value="mock-audio-encoder">mock-audio-encoder</option>
              <option value="msclap:2023">MS-CLAP 2023</option>
            </Select>
          </div>
          <Button className="w-full" type="submit" disabled={disabled}>
            <Upload className="h-4 w-4" />
            上传文件
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
