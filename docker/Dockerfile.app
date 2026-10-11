FROM python:3.10-slim

WORKDIR /workspace

COPY app/requirements.txt /workspace/app/requirements.txt
RUN pip install -r /workspace/app/requirements.txt

COPY model/requirements.txt /workspace/model/requirements.txt
RUN pip install -r /workspace/model/requirements.txt

COPY . /workspace

EXPOSE 7860
CMD ["python", "app/main.py", "--checkpoint", "/workspace/checkpoints/sam_vit_b_01ec64.pth"]
