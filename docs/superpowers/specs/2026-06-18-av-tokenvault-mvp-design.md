# AV-TokenVault MVP 设计规格

## 目标

构建一个本地优先的音视频 Token 化与向量存储原型系统。第一版优先保证完整功能闭环，而不是复杂 UI 或重模型集成。

MVP 需要支持：

- 上传本地视频或音频文件。
- 从视频文件中抽取视频帧和音轨。
- 对音频文件或视频音轨进行切片。
- 通过可插拔 encoder 接口生成占位 embedding。
- 使用 SQLite 保存媒体元数据、抽取产物、任务日志和 embedding。
- 使用简单的 Next.js UI 展示任务状态、抽帧结果、音频片段、日志和入库统计。

## 已确认技术栈

- 后端：Python、FastAPI、SQLAlchemy、SQLite。
- 前端：Next.js、shadcn/ui。
- 本地环境：macOS + conda。
- Python 运行时：使用 Python 3.11 的 conda 虚拟环境。
- 媒体处理：通过 Python 调用 FFmpeg。
- 第一版 encoder：确定性 mock encoder，分别生成图像和音频 embedding。

## MVP 暂不做的内容

- 不做登录或权限系统。
- 不做服务器部署。
- 不做分布式队列、Celery 或 worker 集群。
- 不做复杂多模态问答或模型训练。
- 第一版不依赖 Chroma 或 FAISS。
- 第一版不强制集成严格意义上的离散 token 模型。

## 项目目录结构

```text
AV-TokenVault/
  backend/
    app/
      api/
      core/
      db/
      media/
      encoders/
      pipeline/
      schemas/
      storage/
    tests/
  frontend/
  data/
    uploads/
    extracted/
    sqlite/
  docs/
    superpowers/specs/
```

## 系统架构

系统分为三层：

1. 前端工作台
   - 提供文件上传、处理参数、任务状态、日志、视频帧预览、音频片段表格和统计信息。
   - 处理任务运行时，前端轮询后端任务接口。

2. FastAPI 后端
   - 接收上传文件并保存原始媒体。
   - 创建处理任务。
   - 在本地后台任务中执行媒体解析和 encoding。
   - 向前端提供元数据和抽取产物文件。

3. 本地持久化
   - 上传文件和抽取产物保存在 `data/` 目录下。
   - 元数据、任务状态、日志和 embedding 保存在 SQLite。
   - 提供 `VectorStore` 接口，后续可替换或扩展为 Chroma/FAISS，而不需要重写主流程。

## API 设计

```text
GET  /health
POST /api/media/upload
POST /api/jobs/{job_id}/start
GET  /api/jobs
GET  /api/jobs/{job_id}
GET  /api/jobs/{job_id}/logs
GET  /api/media/{media_id}
GET  /api/media/{media_id}/frames
GET  /api/media/{media_id}/audio-segments
GET  /api/media/{media_id}/stats
GET  /api/files/{artifact_path}
```

`POST /api/media/upload` 同时创建一条 `media_assets` 记录和一条 `pending` 状态的 `processing_jobs` 记录。`POST /api/jobs/{job_id}/start` 启动本地后台处理任务。

`GET /api/files/{artifact_path}` 只允许读取项目 `data/` 目录下的文件。后端必须对请求路径进行规范化和校验，避免客户端读取任意本地文件。

## 数据库设计

### media_assets

- `id`
- `filename`
- `original_path`
- `media_type`
- `mime_type`
- `duration_seconds`
- `file_size`
- `created_at`

### processing_jobs

- `id`
- `media_id`
- `status`
- `progress`
- `mode`
- `frame_interval`
- `segment_seconds`
- `image_encoder`
- `audio_encoder`
- `error_message`
- `created_at`
- `started_at`
- `completed_at`

允许的任务状态：`pending`、`running`、`completed`、`failed`。

### job_logs

- `id`
- `job_id`
- `level`
- `message`
- `created_at`

### video_frames

- `id`
- `media_id`
- `job_id`
- `frame_index`
- `timestamp_seconds`
- `image_path`
- `width`
- `height`

### audio_segments

- `id`
- `media_id`
- `job_id`
- `segment_index`
- `start_seconds`
- `end_seconds`
- `audio_path`
- `duration_seconds`

### embeddings

- `id`
- `media_id`
- `job_id`
- `modality`
- `source_type`
- `source_id`
- `encoder_name`
- `vector_dimension`
- `vector_json`
- `created_at`

MVP 中，`embeddings` 表就是本地向量库原型，用 JSON 保存 mock encoder 生成的向量。

## 处理流程

1. 用户上传 `.mp4`、`.mov`、`.wav` 或 `.mp3` 文件。
2. 后端将文件保存到 `data/uploads/`。
3. 后端判断文件是视频还是音频。
4. 后端创建一个待处理任务。
5. 用户在 UI 中启动处理。
6. 后端执行后台任务：
   - 如果是视频：
     - 读取媒体元信息。
     - 按固定时间间隔抽取视频帧。
     - 提取音轨并转成 WAV。
     - 将音轨切分为多个音频片段。
   - 如果是音频：
     - 必要时先转换为 WAV。
     - 将音频切分为多个片段。
   - 对抽取出的视频帧生成图像 embedding。
   - 对音频片段生成音频 embedding。
   - 保存所有记录和日志。
7. 前端轮询任务状态并展示结果。

## 默认处理参数

- 处理模式：`full`。
- 视频抽帧间隔：`2` 秒。
- 音频切片长度：`5` 秒。
- 单个视频最大抽帧数：`120`。
- 默认图像 encoder：`mock-image-encoder`。
- 默认音频 encoder：`mock-audio-encoder`。

## UI 设计

第一版 UI 是一个简单的本地工作台页面。

页面包含：

- 文件上传控件。
- 处理参数控件。
- 开始处理按钮。
- 任务状态和进度展示。
- 入库统计：视频帧数量、音频片段数量、embedding 数量。
- 视频帧预览网格。
- 音频片段表格。
- 任务日志面板。
- 最近上传媒体或任务的简单列表。

第一版 UI 以清晰、可演示、功能完整为主，视觉精修不是重点。

## 错误处理

- 如果缺少 FFmpeg，后端处理任务失败，并写入可读的任务错误和日志。
- 上传不支持的文件扩展名时，后端直接拒绝。
- 处理失败时，任务状态更新为 `failed`，并保存 `error_message`。
- 前端展示后端返回的错误信息和任务日志。

## 本地运行约束

- MVP 面向单机单用户本地运行。
- 后端可通过 FastAPI background task 或轻量级进程内 worker 执行任务。
- 第一版允许同一时间只处理一个媒体任务。
- 长任务必须通过持久化的任务状态、进度和日志保持可观察。
- 前端和后端只需要配置本地开发端口。

## 可扩展性与可移植性约束

- 图像和音频模型必须通过 encoder 接口接入，主流程不直接依赖具体模型实现。
- 向量写入必须通过 `VectorStore` 接口完成，第一版可落到 SQLite，后续可替换为 Chroma、FAISS 或其他向量库。
- 数据目录、SQLite 路径、默认抽帧间隔、默认音频切片长度、最大抽帧数等参数必须集中配置。
- 运行说明需要覆盖 macOS + conda 的本机运行方式，并保留迁移到 Linux/GPU 机器时需要调整的环境变量、依赖和启动命令。
- 上传文件和抽取产物统一放在 `data/` 下，避免把本地绝对路径写死到业务逻辑中。

## 验证方式

MVP 验证至少覆盖：

- 后端数据库建表和 mock encoder 单元测试。
- 后端 API 冒烟测试：健康检查、上传、任务创建。
- 安装 FFmpeg 后，执行媒体处理流程冒烟测试。
- 前端 scaffold 完成后，执行 lint/build。
- 使用一个短视频和一个短音频进行手动 demo。

## 后续扩展

- 将 SQLite embedding 存储替换或扩展为 Chroma/FAISS。
- 接入真实图像 encoder，例如 OpenCLIP 或 DINOv2。
- 接入真实音频 encoder，例如 Whisper encoder、Wav2Vec2、HuBERT 或 EnCodec。
- 如果导师明确要求严格的 token ID，再加入离散 token 支持。
- 增加相似检索和以文本检索音视频片段等能力。
