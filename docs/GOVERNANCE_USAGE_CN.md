# 项目、实验与环境治理使用指南

本指南对应 1.1.0-beta.1，1.0.0 不包含两个新增入口。
治理能力用于长周期、多人或多方法科研：后续分析能找到当时实际使用的代码、
配置、数据协议和环境，失败重试可追踪，报告恢复和环境变更有可核对的记录。

## 从任务开始

继续用自然语言描述研究任务。`research-guide` 在阶段不明确时协调下一步，
明确的实验、分析或写作任务直接进入对应 skill。项目治理、代码复用和环境
契约按任务需要加载，普通论文阅读无需先初始化项目。

可以直接提出以下任务：

- “盘点这个研究项目的实验、报告和环境，找出缺少来源或无法恢复的记录。”
- “为这组对比实验固定代码、配置和种子；失败后保留原尝试，再启动独立重试。”
- “检查已有环境能否复用；依赖冲突时验证独立候选，保持正在排队的任务绑定。”
- “预演旧项目状态迁移，列出需要停写的任务和回滚条件。”

需要指定入口时使用 `evo-inquiry:project-governance` 或
`evo-inquiry:environment-maintenance`。日常实现中的接口说明、复用和文档新鲜度
检查已嵌入实现相关 skill，无需每次额外调用文档 skill。

## 选择合适的布局

| 布局 | 使用方式 | 产物规则 |
| --- | --- | --- |
| compat-v1 | 默认；现有项目可以没有 project.yaml | 保留既有阶段目录和人工文件，正式引用仍包含固定路径与摘要 |
| governed-v1 | 显式选择，适合多阶段交付和长期复现 | 正文保存为 artifact/revision 的不可变版本；current 只用于导航 |

工作流仍由 `run_state.py` 管理，运行状态使用 `.ei/runs/<workflow_id>.json`。
一次实验设计使用一个 spec；每次真实启动使用独立 execution ID。
同一种子重试记录 retry_of，检查点恢复记录 resumed_from 和 checkpoint_ref。
统计遵守实验开始前指定的纳入规则，失败尝试保留，不能事后挑选最高分。

`current` 不作为正式分析或论文的输入。后续产物记录固定 revision、正文
SHA-256、输入引用和实际审查回执。记录完整不能使结果自动成为 accepted；
独立审查、主张支持程度和实验完整性继续使用既有门禁。

## 工具检查与管理解释器

工具在加载插件的根目录 `tools/` 下，安装缓存路径可能变化。
使用管理解释器安装 [requirements-governance.txt](../requirements-governance.txt)
中的依赖。训练解释器独立，不能为满足登记工具而修改正在使用的训练环境。

下面的只读命令在 EvoInquiry 根目录执行，`/path/to/project` 换为目标项目：

```sh
python tools/project_registry.py --root /path/to/project audit
python tools/project_registry.py --root /path/to/project plan-migration
python tools/environment_registry.py --root /path/to/project inspect --interpreter /path/to/env/bin/python
```

初始化时可显式选择项目 ID 与布局：

```sh
python tools/project_registry.py --root /path/to/project init --project-id research-project --profile governed-v1
```

这些变更只作用于指定项目。旧 `.aris` 状态不会被新写入覆盖；双根冲突、
中断的迁移或布局事务需要先核对。命名空间迁移和产物布局切换使用独立计划，
计划、授权范围、停写确认、备份、进度和校验回执均保留。迁移不改写历史报告
中的证据文本，也不附带删除环境或检查点。

## 环境与资源

先检查真实解释器、依赖、导入来源和消费者，能兼容复用就保持现有冻结版本。
需要变更时，用现有 conda/uv 工具建立独立候选，保存完整依赖差异及元数据、
导入、数值和代表性消费者四层实际检查回执，再在获准范围内提升和绑定。
`--required-consumers` 可在候选登记和提升时要求覆盖指定消费者。

排队或运行中的任务保持固定环境；超时 lease 需要真实任务终止证据才可释放。
论文复现 pin 独立于 lease，结束训练不自动取消复现保护。环境退休工具只输出
计划。现有检查点策略继续控制权重保留、恢复验证、最优模型归档和存储峰值。
可变缓存使用独立空间或经验证的锁与原子发布，实际跨项目共享才需要所有者索引。

## 支持范围与候选验证

治理写入需要文件系统提供可靠排他锁和本地 rename/fsync 语义。工具会先探测
锁是否真正排斥另一个写者，不可靠时停止写入。当前会话工作区的虚拟挂载实际
未通过探测；`/tmp` 的本地文件系统通过，完整试点在该目录验证后归档证据。
这一结果只描述本次运行环境，不代表所有同名路径或文件系统均有此限制。
真实单卡 GPU 短训练已验收，不能推广为多卡或大规模训练认证。Windows 使用独立发布门槛；网络文件系统和 SSH/screen 队列仍需部署验收。持久存储和实际探测命令见[部署指南](DEPLOYMENT_GUIDE.md)。

开发候选先通过临时 `.agents/skills` 验证，后续已用正式插件来源和 `skills/list` 验证安装与回滚。安装时应替换现有插件来源。新旧来源同时启用会重复展示同名 skill，Codex 不合并它们。
该机制参考官方 [本地 skill 发现说明](https://learn.chatgpt.com/docs/build-skills)
与 [App Server 接口](https://learn.chatgpt.com/docs/app-server)，并以本机实际输出核对。

实施顺序见[升级实施计划](UPGRADE_IMPLEMENTATION_CN.md)。
