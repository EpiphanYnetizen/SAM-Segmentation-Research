# 3 方法与改进

基座模型选取 SAM ViT-B / MobileSAM。先做零样本单点提示分割，作为基线；后在 GT 点提示下、冻结主干、对 image encoder 的 query/value 层挂 LoRA，并微调 mask decoder。辅助对照为 DINOv2 特征（可选），不作为主实验结果。
