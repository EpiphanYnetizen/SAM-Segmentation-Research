# Docker（组长，可选）

优先级排在模型跑通之后。目标是把 Gradio demo 打包，方便答辩现场和其他成员复现。

```bash
docker compose -f docker/docker-compose.yml up --build
# 浏览器打开 http://localhost:7860
```

## 两个必须注意的点

- 权重不进镜像。宿主机挂载到 `/workspace/checkpoints`。
- 容器里的 Gradio 必须监听 `0.0.0.0`，否则容器外访问不到。`app/main.py` 已支持 `--host`，compose 里传 `--host 0.0.0.0` 即可。

## 它和网页的关系

Docker 不是在浏览器里再套一层。它只是把「跑 Gradio 的那台机器」换成容器：

```text
宿主机浏览器  http://localhost:7860
      |  端口映射 7860:7860
      v
容器内 Gradio (0.0.0.0:7860)
```

对外看起来和直接 `python app/main.py` 完全一样，区别只是环境被固定住了，换台电脑也能跑起来。
