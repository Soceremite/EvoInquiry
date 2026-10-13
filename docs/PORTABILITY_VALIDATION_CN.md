# 1.1.0-beta.2 兼容性与验证边界

本次更新根据 beta.1 的 macOS 目录别名及 Windows 内建模块故障，检查了同类
平台假设。保留原有 83 个工作流主体、86 个 Codex 入口和检查点工具字节；新增
回归集中在真实解释器、消费者覆盖、源码解码和治理路径，不改变科研审查门禁。

## 修复与对应回归

| 问题 | 修复后的行为 | 实际回归 |
| --- | --- | --- |
| 消费者 ID 跨层合并 | 只有成功的 consumers 层回执计入要求的覆盖 | metadata/imports/numerical 的 ID、部分覆盖、消费者失败均拒绝；旧冻结记录及绑定字节保留 |
| 解释器随 cwd/PATH 改变 | 固定已验证的绝对入口，保留 venv 最后一级入口 | 中文/空格 venv、相对入口、PATH 名称、不同 cwd 的快照启动；真实 prefix 与依赖一致 |
| 导入输出污染 JSON | 指纹使用唯一绑定帧，日志独立捕获 | 中文 stdout/stderr、普通通知、日志中的 JSON、重复帧、非法 JSON/指纹、非零退出、超时；只读探测不初始化状态 |
| namespace 来源缺失 | 新指纹记录模块类型、origin、搜索位置及 prefix | 真实 `.pth` 改变 namespace 来源后停止启动；内建、文件与扩展模块可记录 |
| 源码被默认编码解码 | 按 Python 编码声明或 BOM 读取 | UTF-8 中文、UTF-8 BOM、Latin-1 合法声明；非法编码与语法仍拒绝；原字节摘要一致 |
| 安装断言比较别名字符串 | 断言两侧都使用真实目录身份 | 目录别名下运行原 Codex/Copilot 安装、更新、卸载及 agent 部署契约 |
| Junction 未被识别 | 状态、证据和 doctor 拒绝重定向路径 | 原生 NTFS 构造 `.ei`、`.aris`、迁移、报告和源码 Junction；外部哨兵文件保持原字节 |
| 保留名称与大小写冲突 | 拒绝保留组件和盘符相对引用，绑定不被大小写别名覆盖 | CON/NUL/COM1/LPT1、扩展名、尾点/空格、驱动器/流引用；原生 Windows 消费者冲突拒绝 |

核心用例在 [test_portability_governance.py](../tests/test_portability_governance.py)，
安装器目录别名用例在 [test_installer_alias_paths.py](../tests/test_installer_alias_paths.py)。
修改原安装测试的理由与摘要登记在保留契约中，原冻结基线摘要未被改写。
治理路径守卫不限制安装器自身管理的 skill 链接。

## 历史指纹与入口兼容

默认探测生成 fingerprint version 2。历史记录未声明版本时，验证继续生成
version 1 的原字段，与固定记录逐项比较，不通过补字段或重写 JSON 伪造升级。
旧格式的 namespace 来源覆盖仍较窄；需要新覆盖时，单独验证并冻结新环境版本。
历史相对入口在与已固定的实际解释器一致时恢复为绝对入口用于本次核验和启动，
原记录保持不变。不一致或无法绑定的解释器需要新版本，不能猜测后启动。

不要对 venv 可执行入口整体调用 `resolve()`：这可能进入基础 Python。
`inspect --diagnostics` 提供捕获的导入 stdout/stderr 和真实退出码；默认 inspect
仍返回指纹对象。模块来源元数据不等于第三方包所有文件的内容完整性认证，
消费者 ID 也不证明命令真的执行了所声明的方法；命令必须包含有效接口测试。

## 平台验收

主分支和发布流程都执行 Linux/macOS 完整 pytest。原生 Windows 的 powershell.exe
与 pwsh 两组还执行全部兼容性用例、安装器、文件系统 doctor 及项目到报告闭环。
NTFS 用例也验证 Python 3.10/3.11 所需的 reparse-tag 回退识别；不依赖仅 Python
3.13 提供的保留名称 API。发布需要四组平台检查全部成功。

本机 Linux 的 Windows 跳过项不能作为 Windows 通过证据，实际结果以对应源码
的 [GitHub Actions](https://github.com/Soceremite/EvoInquiry/actions) 为准。
beta.1 的 GPU、离线安装及自然语言验收属于此前来源，详见
[固定历史记录](https://github.com/Soceremite/EvoInquiry/blob/v1.1.0-beta.1/release-validation.json)。
本次不将此前试点重新记为新的 GPU 或行为评测。
