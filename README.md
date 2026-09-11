# AV-TokenVault

AV-TokenVault 是一个本地运行的音视频 Token 化与向量入库原型系统。当前重点是跑通完整功能闭环：上传音视频、抽取帧和音频片段、生成 embedding、写入 SQLite，并在简单 UI 中展示结果。

系统现在默认使用 mock encoder，方便在 Mac 本机稳定运行；同时已经预留 transcript、text embedding 和本地检索能力，可以作为后续接 Whisper、BGE-M3、CLIP、CLAP 等真实模型的 RAG-ready 数据底座。

## 当前技术栈

- 后端：Python 3.11、FastAPI、SQLAlchemy、SQLite
- 前端：Next.js、TypeScript、shadcn/ui 风格组件
- 媒体处理：FFmpeg
- 第一版模型：mock image/audio encoder
- RAG-ready 扩展：mock transcriber、mock text embedder、SQLite 本地相似检索
- 本地环境：macOS + conda

## 本机环境准备

安装 FFmpeg：

```bash
brew install ffmpeg
```

创建 conda 环境：

```bash
conda env create -f environment.yml
conda activate av-tokenvault
```

## 启动后端

```bash
conda activate av-tokenvault
./scripts/dev-backend.sh
```

如果要启用真实语音转写和真实文本 embedding：

```bash
conda activate av-tokenvault
./scripts/dev-backend-real.sh
```

默认真实模型模式使用：

- `faster-whisper-base`
- `sentence-transformers:BAAI/bge-small-zh-v1.5`

如果要尝试更重的 BGE-M3：

```bash
AV_TOKENVAULT_DEFAULT_TEXT_ENCODER=sentence-transformers:BAAI/bge-m3 ./scripts/dev-backend-real.sh
```

## 启动前端

```bash
npm --prefix frontend install
./scripts/dev-frontend.sh
```

前端默认访问 `http://127.0.0.1:8000`。如果后端地址变化，可以设置：

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## 验证命令

后端测试：

```bash
conda run -n av-tokenvault pytest -v
```

前端检查：

```bash
cd frontend
npm run lint
npm run build
```

如果前端 dev server 正在运行，优先只跑 `npm run lint`。需要跑 `npm run build` 时，建议先停掉前端 dev server，避免 Next.js 的开发缓存和构建缓存互相影响。

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

## 数据目录

运行时数据统一放在 `data/` 下：

- `data/uploads/`：上传的原始媒体
- `data/extracted/`：抽取的视频帧、音轨和音频片段
- `data/sqlite/`：SQLite 数据库

这些目录中的运行时文件默认不提交到 git，只保留 `.gitkeep`。

## 可扩展性说明

- 图像和音频模型通过 `backend/app/encoders/` 下的接口接入。
- Transcriber 和文本 embedding 模型同样通过 encoder registry 接入。
- 向量写入通过 `VectorStore` 接口完成，第一版落到 SQLite，后续可以替换为 Chroma、FAISS 或远程向量库。
- 目录、默认抽帧间隔、音频切片长度、最大帧数等参数集中在后端配置中。
- 视频抽帧会优先使用用户设置的抽帧间隔；如果长视频按该间隔会超过最大帧数，系统会自动拉大实际抽帧间隔，让最多 600 帧均匀覆盖整段视频。
- 前端请求都集中在 `frontend/lib/api.ts`，迁移后端地址时优先调整 `NEXT_PUBLIC_API_BASE_URL`。
- 运行时产物只放在 `data/` 下，避免业务代码绑定本机绝对路径。

## 模型路线

当前默认模式：

- `mock-image-encoder`
- `mock-audio-encoder`
- `mock-transcriber`
- `mock-text-embedder`

推荐的真实模型升级路线：

- 语音转文字：Whisper 或 faster-whisper
- 文本 embedding：BGE-M3，中文和多语言检索更合适
- 视频帧检索：CLIP / OpenCLIP / SigLIP
- 非语音音频事件检索：CLAP

本机已验证可运行的模型/adapter：

- `faster-whisper-base`：真实音频转写。
- `sentence-transformers:BAAI/bge-small-zh-v1.5`：512 维中文文本 embedding，推荐本机默认演示。
- `sentence-transformers:BAAI/bge-m3`：1024 维多语言文本 embedding，可运行但首次加载更慢。
- `open-clip:ViT-B-32:laion2b_s34b_b79k`：512 维视频帧 embedding。
- `msclap:2023`：1024 维音频事件 embedding。

项目当前不是完整 RAG 聊天系统，而是音视频 token 化、向量入库和可检索数据底座。后续可以基于 transcript、frame、audio segment 和 embedding 继续扩展问答或 RAG 应用。

## 迁移到 Linux/GPU 机器

第一版先面向本机运行。后续迁移到实验室 Linux/4090 机器时，优先保持同样的目录结构和启动命令，只需要调整：

- Python/conda 环境和 PyTorch/CUDA 版本
- FFmpeg 安装方式
- 后端监听地址和前端 `NEXT_PUBLIC_API_BASE_URL`
- encoder 适配器，从 mock encoder 切换到真实模型

如果要让局域网其他机器访问后端，可以这样启动：

```bash
AV_TOKENVAULT_HOST=0.0.0.0 AV_TOKENVAULT_PORT=8000 ./scripts/dev-backend.sh
```

然后在前端设置实际后端地址：

```bash
NEXT_PUBLIC_API_BASE_URL=http://<服务器IP>:8000 npm run dev
```
