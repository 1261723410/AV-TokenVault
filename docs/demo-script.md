# AV-TokenVault 演示脚本

## 演示目标

展示系统已经完成老师要求的原型闭环：

```text
输入视频/音频 -> 抽帧/抽音轨 -> 音频切片 -> token/embedding -> SQLite 入库 -> UI 展示/检索
```

## 启动

后端：

```bash
conda activate av-tokenvault
./scripts/dev-backend.sh
```

前端：

```bash
./scripts/dev-frontend.sh
```

打开：

```text
http://localhost:3000
```

## 演示步骤

1. 上传一个短视频或短音频。
2. 设置抽帧间隔和音频切片长度。
3. 点击上传后，在任务状态面板点击开始处理。
4. 等任务状态变为 `completed`。
5. 展示入库统计：
   - 视频帧数量
   - 音频片段数量
   - 转写片段数量
   - embedding 数量
6. 展示视频帧预览。
7. 展示音频片段表。
8. 展示转写片段。
9. 在本地检索框输入一段文字，展示匹配到的 transcript 结果。

## 汇报时可以强调

当前系统已经把非结构化音视频变成结构化记录：

- 原始媒体文件保存在 `data/uploads/`。
- 抽帧、音轨和音频切片保存在 `data/extracted/`。
- 元数据、任务、日志、帧、音频片段、transcript 和 embedding 保存在 SQLite。
- 后续可以把 mock encoder 换成 Whisper、BGE-M3、CLIP、CLAP 等真实模型。

## 注意

旧任务是在 transcript 功能加入前处理的，因此旧任务不会自动出现转写片段。需要重新上传并处理一个新任务，才会生成 transcript 和 text embedding。
