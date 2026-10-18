# Docker（组长，可选）

优先级排在模型跑通之后。目标是把 Gradio demo 打包，方便答辩现场和其他成员复现。

```bash
docker compose -f docker/docker-compose.yml up --build
# 浏览器打开 http://localhost:7860
```

## 两个必须注意的点

- **权重不进镜像。** 走 volume 挂载：宿主机仓库的 `checkpoints/` -> 容器 `/workspace/checkpoints`（只读）。
- **容器里的 Gradio 必须监听 `0.0.0.0`**，监听 `127.0.0.1` 的话容器外访问不到。`Dockerfile.app` 的 CMD 已经带上 `--host 0.0.0.0`，别删。

## 构建上下文

build context 是仓库根目录 `..`，所以根目录的 `.dockerignore` 决定什么不进镜像：`checkpoints/`、`data/raw/`、`outputs/`、`.venv/` 全部排除。**新增大的本地目录时记得同步加进 `.dockerignore`**，否则镜像会膨胀到几个 G。

## 本仓库不用 .env

没有 `env_file`，也不需要。唯一的可调项是权重路径，走 volume + CLI 参数就够了。

## 它和网页的关系

Docker 不是在浏览器里再套一层。它只是把「跑 Gradio 的那台机器」换成容器：

```text
宿主机浏览器  http://localhost:7860
      |  端口映射 7860:7860
      v
容器内 Gradio (0.0.0.0:7860)
```

对外看起来和直接 `python app/main.py` 完全一样，区别只是环境被固定住了，换台电脑也能跑起来。
