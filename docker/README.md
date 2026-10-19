# Docker（组长，可选）

优先级位于模型可运行之后。目标是将 Gradio demo 打包，便于答辩现场及其他成员复现。

```bash
docker compose -f docker/docker-compose.yml up --build
# 浏览器访问 http://localhost:7860
```

## 注意事项

- 权重不打包进镜像，通过 volume 挂载：宿主机 `checkpoints/` -> 容器 `/workspace/checkpoints`（只读）。
- 容器内 Gradio 需监听 `0.0.0.0`；`Dockerfile.app` 的 CMD 已配置 `--host 0.0.0.0`，需保留。
- 构建上下文为仓库根目录，`.dockerignore` 已排除 `checkpoints/`、`data/raw/`、`outputs/`、`.venv/` 等；新增大体积目录时需同步更新，否则镜像体积会明显增大。

## 环境变量说明

本仓库不使用 `.env` 或 `env_file`。唯一可调项为权重路径，通过 volume 与 CLI 参数完成。

## 与网页访问的关系

Docker 不增加额外的访问层级，仅将「运行 Gradio 的主机」替换为容器：

```text
宿主机浏览器  http://localhost:7860
      |  端口映射 7860:7860
      v
容器内 Gradio (0.0.0.0:7860)
```

外部访问方式与直接运行 `python app/main.py` 一致，区别在于依赖与运行环境被固化。
