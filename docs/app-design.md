# 前后端设计（可视化 Demo）

> **状态：设计稿，未实现。** 仓库里没有 `app/api/` 和 `app/web/`，
> 当前可运行的是 `app/main.py`（Gradio 骨架，推理未接入）。
> 本文描述的是二期方案，按里程碑推进前请先完成模型侧。

本文只描述 `app/` 的内部设计，不改变根 [`README.md`](../README.md) 里的模块边界：`app/` 只读推理结果，不训练、不评测。

## 0. 当前入口

`app/main.py` 目前是 Gradio 界面骨架，`render_mask()` 尚未接入真实 SAM，提交时会明确报错：

```bash
pip install -r app/requirements.txt
python app/main.py --checkpoint checkpoints/sam_vit_b_01ec64.pth
# 浏览器访问 http://localhost:7860
```

接入推理时只改 `render_mask()` 内部（详见 [`../app/README.md`](../app/README.md)），
部署参数保持 `--checkpoint` / `--host` / `--port` 不变。本文的 Vue + FastAPI 属于二期方案。

## 1. 目标与非目标

目标：

- 上传一张食堂照片，点一下某个菜，返回该物体的 mask。
- 自动模式一次给出图中若干物体，按面积排序展示。
- 结果可叠加、可切换透明度、可导出 PNG。
- 单卡 4G 显存可稳定运行，不因并发请求爆显存。

非目标：

- 不做用户系统、登录、数据库。
- 不做在线训练或标注。
- 不做多模型热切换（先用启动参数指定一个 checkpoint）。

## 2. 总体架构

```text
浏览器（Vue 3 + Vite）
   │  HTTP  /api/v1/*
   ▼
FastAPI（单进程、单 worker）
   │  进程内函数调用
   ▼
SAM service（启动时加载一次，推理加锁）
   │
   └── checkpoints/sam_vit_b_01ec64.pth
```

开发环境：Vite dev server 跑在 5173，把 `/api` 代理到 FastAPI 的 8000。
生产环境：`npm run build` 产出静态文件，由 FastAPI 用 `StaticFiles` 托管，一个容器、一个端口，避免再引入 Nginx。

## 3. 技术选型

| 层 | 选择 | 理由 |
|---|---|---|
| 前端 | Vue 3 + Vite + 原生 CSS | 组员已会 Vue；不引 UI 库，避免“一眼 Element Plus”的模板感 |
| 后端 | FastAPI + Uvicorn + Pydantic | 与 Python 模型同进程，零跨语言成本 |
| 推理 | `segment_anything` 的 `SamPredictor` | 与现有 `model/zero_shot_inference.py` 一致 |
| 图像 | Pillow + OpenCV | 编解码 mask、叠加预览 |
| 部署 | 多阶段 Docker（Node 构建 + Python 运行） | 一个镜像，避免前后端两个容器 |

不使用 Spring Boot + MyBatis：本项目没有业务数据库，模型在 Python 进程内，Java 层只能做转发，净增一套依赖和部署成本。若课程明确要求三层架构，再把 Spring Boot 作为可选 BFF，不进入主链路。

## 4. 目录结构

```text
app/
  main.py                 # 保留现有 Gradio 版本，作为应急演示
  api/
    __init__.py
    main.py               # FastAPI 入口、路由、静态文件托管
    schemas.py            # 请求/响应模型
    inference.py          # SAM 加载、加锁、点/框/自动推理
    mock.py               # MOCK=1 时的假推理，供前端联调
  web/
    package.json
    vite.config.js
    index.html
    src/
      main.js
      App.vue
      styles/tokens.css
      api/client.js
      composables/
        useSegmentation.js
        useCanvasCoords.js
      components/
        AppHeader.vue
        UploadPanel.vue
        ImageStage.vue
        ToolBar.vue
        ResultPanel.vue
        MaskList.vue
        ClassLegend.vue
```

## 5. API 契约

统一前缀 `/api/v1`，全部返回 JSON。错误统一格式：

```json
{"error": {"code": "GPU_BUSY", "message": "当前有推理任务，请 2 秒后重试"}}
```

### GET /api/v1/meta

返回类别、模型、设备信息，前端启动时拉一次。

```json
{
  "model": "sam_vit_b",
  "device": "cuda",
  "classes": [
    {"id": 0, "name": "background", "color": "#0B0F14"},
    {"id": 1, "name": "meat", "color": "#F87171"},
    {"id": 2, "name": "fish", "color": "#38BDF8"},
    {"id": 3, "name": "vegetable", "color": "#4ADE80"},
    {"id": 4, "name": "rice", "color": "#FBBF24"},
    {"id": 5, "name": "other", "color": "#A78BFA"},
    {"id": 255, "name": "ignore", "color": "#64748B"}
  ]
}
```

### POST /api/v1/segment/point

`multipart/form-data`：

| 字段 | 类型 | 说明 |
|---|---|---|
| `image` | file | 原图，最大 15 MB |
| `points` | string | JSON，`[[x, y], ...]`，原图像素坐标 |
| `labels` | string | JSON，`[1, 0, ...]`，1 前景、0 背景 |
| `multimask` | bool | 是否返回 3 个候选，默认 true |

响应：

```json
{
  "request_id": "uuid",
  "width": 1279,
  "height": 1706,
  "masks": [
    {"index": 0, "score": 0.977, "area": 123456,
     "bbox": [120, 340, 480, 390], "png_base64": "..."}
  ],
  "timing_ms": {"encode": 812, "decode": 34, "total": 861}
}
```

### POST /api/v1/segment/auto

字段：`image`。内部用 `SamAutomaticMaskGenerator`，`points_per_side=12`，按面积降序，只返回前 12 个，避免响应过大。

```json
{
  "request_id": "uuid",
  "width": 1279,
  "height": 1706,
  "masks": [
    {"index": 0, "score": 0.93, "area": 200000, "bbox": [0,0,10,10], "png_base64": "..."}
  ],
  "timing_ms": {"total": 28400}
}
```

### POST /api/v1/segment/box（可选）

字段：`image`、`box`（JSON，`[x1, y1, x2, y2]`）。用于拖框提示，第二阶段再做。

### 约定

- 坐标一律使用**原图像素**。前端负责把画布坐标换算回原图坐标，后端不做缩放换算。
- mask 统一用 PNG + base64，前端直接画到 canvas，不落临时文件。
- 单请求超时 60 秒；自动模式单独放宽到 120 秒。
- 超过 15 MB 或非图片直接 413/415。

## 6. 并发与显存

4G 显存下不能并跑两个推理：

- 全局一把 `threading.Lock`，拿不到锁立即返回 429 + `Retry-After: 2`。
- Uvicorn 只起 1 个 worker，禁止 `--workers N`。
- `torch.cuda.empty_cache()` 只在启动后调用一次，不要每请求调用，反而拖慢。
- 自动模式 `points_per_side=12`，不要用 32；否则单图要几分钟。
- 上传图长边超过 2048 时，服务端先等比缩小再推理，响应里返回 `scale`，前端按比例映射回原图。

## 7. 前端设计

### 7.1 布局

```text
┌──────────────────────────────────────────────────────────────┐
│ Header：项目名 · 模型徽章 · 设备 · 模式切换                    │
├───────────────┬──────────────────────────────┬───────────────┤
│ 左栏 280px    │ 中央画布（自适应）            │ 右栏 320px    │
│ 上传 / 示例   │ 图片 + mask 叠加 + 点标记      │ 运行信息      │
│ 提示设置      │ 底部工具栏                    │ mask 列表     │
│ 类别图例      │                              │ 导出按钮      │
└───────────────┴──────────────────────────────┴───────────────┘
```

窄于 1200px 时右栏折叠为抽屉；窄于 800px 时上下堆叠，画布优先。

### 7.2 视觉令牌

```css
--bg:        #0B0F14;
--surface:   #121821;
--surface-2: #18202B;
--border:    #223041;
--text:      #E6EDF3;
--muted:     #94A3B8;
--accent:    #5EEAD4;
--accent-2:  #F59E0B;
--danger:    #F87171;
--radius:    12px;
--shadow:    0 12px 32px rgba(0, 0, 0, 0.35);
```

字体：`Inter, "Noto Sans SC", system-ui`。指标数字用 `font-variant-numeric: tabular-nums`。

深色底的理由：食堂照片色彩饱和，深色界面能让菜品颜色跳出来，也能掩盖 mask 叠加的杂色。

### 7.3 交互

- 点提示：左键加前景点（青色），`Shift + 左键`加背景点（红色），`Esc` 清空。
- 每次加点后 300 ms 防抖发起请求，避免连点打爆显存。
- 画布显示十字准星与当前坐标；点用 8px 圆点 + 序号。
- 自动模式：按钮触发，返回后按面积排序；点击列表项高亮对应 mask。
- 视图切换：原图 / 叠加 / 纯 mask；透明度滑杆 0–100%。
- 导出：叠加图 PNG、原始 mask PNG、复制指标 JSON。

### 7.4 状态

```text
idle → uploading → encoding → ready → segmenting → result
                                      ↘ error
```

- `encoding` 显示“图像编码中…”，用骨架屏覆盖画布，不阻塞工具栏。
- `segmenting` 显示进度条的不确定态，并禁用重复提交。
- `error` 用右下角 toast，附“重试”按钮，不弹模态框。

### 7.5 空状态与示例

首次进入显示虚线拖拽区，附 3 张内置示例图（`app/web/public/samples/`），点击即可加载，避免用户还要自己找图。

## 8. Mock 优先

后端支持 `MOCK=1`：不加载 SAM，按请求里的点生成一个椭圆 mask，`score` 随机在 0.8–0.95，`timing_ms` 用假值。前端从第一天就能完整联调，不必等模型训练完。

```bash
MOCK=1 uvicorn app.api.main:app --reload --port 8000
npm --prefix app/web run dev
```

## 9. 开发与部署

开发：

```bash
# 终端 1
.\.venv\Scripts\python.exe -m uvicorn app.api.main:app --reload --port 8000
# 终端 2
npm --prefix app/web run dev
```

生产镜像采用多阶段构建：

1. `node:20-alpine` 执行 `npm ci && npm run build`。
2. `python:3.10-slim` 安装 `app/requirements.txt` 与 `model/requirements.txt`。
3. 拷贝 `app/web/dist`，FastAPI 用 `StaticFiles` 托管。
4. `CMD uvicorn app.api.main:app --host 0.0.0.0 --port 7860`。

GPU 通过 compose 的 device reservation 暴露；Windows 上需要 Docker Desktop 的 WSL2 后端。

## 10. 里程碑

| 阶段 | 产出 | 预估 |
|---|---|---|
| M1 | API 契约 + Mock 后端 + Vue 空壳 | 0.5 天 |
| M2 | 上传、画布、坐标换算、点提示叠加 | 1 天 |
| M3 | 自动模式、结果列表、导出 | 0.5 天 |
| M4 | 接真实 SAM、并发锁、错误处理 | 0.5 天 |
| M5 | 视觉打磨、响应式、Docker | 1 天 |

## 11. 风险

- 坐标换算是最容易出错的地方：画布有 `object-fit` 缩放，必须用原图尺寸与显示尺寸的比值换算，并写单元测试。
- 自动模式响应体可能很大：限制返回前 12 个 mask。
- 4G 显存：只允许单请求；批量评测不要走这个 API，直接跑离线脚本。
- Gradio 版本保留但不再演进，避免两套 UI 同时维护。

## 12. Docker

Docker 的目标是把正式 UI 打包，便于答辩现场和其他成员复现。优先级在模型可运行之后。

```bash
docker compose -f docker/docker-compose.yml up --build
# 浏览器访问 http://localhost:7860
```

注意：

- 权重不打包进镜像，通过 volume 挂载：宿主机 `checkpoints/` -> 容器 `/workspace/checkpoints`（只读）。
- 容器内服务监听 `0.0.0.0`；`Dockerfile.app` 的 CMD 已配置 `--host 0.0.0.0`，需保留。
- 构建上下文是仓库根目录，`.dockerignore` 已排除 `checkpoints/`、`data/raw/`、`outputs/`、`.venv/` 等；新增体积大的目录时同步更新。
- 本仓库不使用 `.env` 或 `env_file`，权重路径通过 volume 与 CLI 参数指定。
