# AV-TokenVault

AV-TokenVault 是一个本地运行的音视频 Token 化与向量入库原型系统。第一版重点是跑通完整功能闭环：上传音视频、抽取帧和音频片段、生成 mock embedding、写入 SQLite，并在简单 UI 中展示结果。

## 当前技术栈

- 后端：Python 3.11、FastAPI、SQLAlchemy、SQLite
- 前端：Next.js、TypeScript、shadcn/ui 风格组件
- 媒体处理：FFmpeg
- 第一版模型：mock image/audio encoder
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
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认访问 `http://127.0.0.1:8000`。如果后端地址变化，可以设置：

```bash
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

## 数据目录

运行时数据统一放在 `data/` 下：

- `data/uploads/`：上传的原始媒体
- `data/extracted/`：抽取的视频帧、音轨和音频片段
- `data/sqlite/`：SQLite 数据库

这些目录中的运行时文件默认不提交到 git，只保留 `.gitkeep`。

## 可扩展性说明

- 图像和音频模型通过 `backend/app/encoders/` 下的接口接入。
- 向量写入通过 `VectorStore` 接口完成，第一版落到 SQLite，后续可以替换为 Chroma、FAISS 或远程向量库。
- 目录、默认抽帧间隔、音频切片长度、最大帧数等参数集中在后端配置中。

## 迁移到 Linux/GPU 机器

第一版先面向本机运行。后续迁移到实验室 Linux/4090 机器时，优先保持同样的目录结构和启动命令，只需要调整：

- Python/conda 环境和 PyTorch/CUDA 版本
- FFmpeg 安装方式
- 后端监听地址和前端 `NEXT_PUBLIC_API_BASE_URL`
- encoder 适配器，从 mock encoder 切换到真实模型
