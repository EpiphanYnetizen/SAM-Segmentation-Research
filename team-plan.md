# SAM-Segmentation-Research 团队计划书

> 课程：深度学习课程设计 2026 秋季
> Track：Research · No.2 Large Visual Model
> 报名截止：2026-10-11；开题：2026-10-25 前交 3 页 PPT + 3 分钟视频

## 0.5 硬节点：10 月 25 日前提交开题（优先级最高）

| 交付物 | 要求 | 负责人 | 协作 |
|---|---|---|---|
| `开题报告.mp4` | 3 分钟 | 组长 PM 录制 | A 提供数据页素材，B 提供模型页素材 |
| `开题报告.ppt` | 恰好 3 页 | 组长 PM 汇总 | 第 1 页全员信息；第 2 页 A 的数据；第 3 页 B 的模型 |
| 发送邮件 | 课程指定邮箱，主题 `深度学习_[姓名1]_[姓名2]_[姓名3]_选题_2` | 组长 PM | 全组确认姓名、班级、组长 |

> 10/25 是硬截止，优先于 W2 的其他训练任务；10/24 前完成成品并留出检查命名缓冲区。

## 0. 人员与角色

| 角色 | 负责模块 | 成员 |
|---|---|---|
| 组长 / PM | 统筹 + mask decoder 微调与消融、`app/`、`scripts/`、`docker/`、报告/PPT/视频 | 黄闻喆 |
| 组员 A · 数据与评测 | `data/`、`evaluation/` | 待填姓名 |
| 组员 B · 模型与训练 | SAM 加载与 zero-shot、image encoder LoRA、checkpoint | 待填姓名 |

### 贡献值建议（合计 100）

| 成员 | 建议贡献值 | 分配依据 |
|---|---|---|
| 组长 / PM | 34 | mask decoder 微调、消融实验、推理集成、报告/PPT/视频、总体兜底 |
| 组员 A | 33 | 数据采集标注 + 指标与失败案例 |
| 组员 B | 33 | SAM 部署、zero-shot 推理、image encoder LoRA 与 checkpoint |

> 答辩参与情况计入贡献分；最终以上面数字为准，答辩前可微调，但求和必须为 100。

## 1. 每周目标

### W1：10/12 - 10/17

| 角色 | 交付 |
|---|---|
| PM | 发报名邮件、建仓库、定接口契约、预装依赖、跑通 mask decoder 前向 |
| A | 定类别清单（`data/categories.yaml`）、开始自采照片、搭好 Label Studio |
| B | 读 SAM 论文、下载 `sam_vit_b` / MobileSAM 权重、跑通官方 demo |

### W2：10/18 - 10/24

| 角色 | 交付 |
|---|---|
| PM | 10/24 前完成开题 PPT 与视频成品，10/25 前发送；同时搭好 mask decoder 微调脚手架 |
| A | 标注完成 80-120 张（约 400-600 个实例）、导出 mask、划分 7:1:2 |
| B | 完成 zero-shot 批量推理，输出 `outputs/zero_shot` |

### W3：10/25 - 10/31

| 角色 | 交付 |
|---|---|
| PM | 训练 mask decoder（`model/train_mask_decoder.py`）并跑消融，产出 v1 checkpoint |
| A | 零样本评测 + 失败案例图鉴（小目标/遮挡/反光/细长/透明） |
| B | LoRA 微调 image encoder，产出 v1 checkpoint 并与 PM 对齐 |

### W4：11/1 - 课程截止前

| 角色 | 交付 |
|---|---|
| PM | mask decoder 组 vs encoder 组对比固化、最终报告/PPT/视频、答辩演练 |
| A | 补充微调后评测、对比表与边界 F1 |
| B | image encoder 消融、最终 checkpoint 固化 |

## 2. 接口契约

统一维护在 [`docs/data-protocol.md`](docs/data-protocol.md)（唯一真源）。这里不再抄一份，避免两处不一致。

## 3. 课程硬性要求对照

| 课程要求 | 本计划对应 |
|---|---|
| Research 禁现成 API，除非蒸馏教师模型 | 全部本地 SAM/SAM2 推理与后训练 |
| 至少 SFT/RLHF/OPD/OPSD 其一，通常 LoRA | LoRA 微调 mask decoder / image encoder |
| 自采数据 + 自定义类别，加 5-10 分 | `data/raw` 自采 + `data/categories.yaml` |
| 3 页 PPT：题目成员 / 数据来源 / 模型改进 | 10/25 前由 PM 交付 `开题报告.ppt` |
| 3 分钟视频 | 10/25 前由 PM 交付 `开题报告.mp4`，演讲稿单独保存、不进仓库 |

## 4. 风险预案

| 风险 | Plan B |
|---|---|
| 无 GPU / 显存不够 | 用 `SAM-ViT-B` 或 MobileSAM；申请院计算资源或免费云 GPU |
| 标注过慢 | 先标 4 类共 60-80 张，抢核心实验闭环；剩下的当增量 |
| 微调后不比 zero-shot 好 | 这也是结论；把失败案例和边界分析作为核心贡献 |
| SAM 权重下载慢 | 提前用镜像/HF 下载并放 `checkpoints/`，成员间共享 |
| 模型要求像语言模型的 SFT/RLHF 表述 | 开题前发邮件和老师确认视觉模型 LoRA 是否满足要求 |

## 5. 会议规则

- 每周一次 30 分钟周会，只聊卡点和决策，不开状态会。
- 组员 A/B 每次开会前在 `docs/` 更新自己模块进度。
- PR 至少组长 review 后合入；开题周允许快速合并。

## 6. 零经费 / 工具方案

| 项 | 方案 |
|---|---|
| 标注 | Label Studio（本地 Docker / pip） |
| GPU | 自用电脑、院里免费资源、Colab/Kaggle 免费额度 |
| 文档 | Markdown + Git，最后由组长生成 PPT/PDF |
| 视频 | 录屏 + 剪映，不追求特效 |
