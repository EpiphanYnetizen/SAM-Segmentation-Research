# Docker（组长 PM，可选）

部署优先级排在模型跑通之后。目标是把 Gradio demo、零样本推理和两种微调实验打包，方便答辩现场和其他成员复现。创建本目录由组长负责。

## 构建与运行

```bash
docker compose -f docker/docker-compose.yml up --build
# http://localhost:7860
```

模型权重请在宿主机挂载到 `/workspace/checkpoints`。
