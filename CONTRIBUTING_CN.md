# 参与 EvoInquiry

[English](CONTRIBUTING.md)

通过本仓库的 Issues 和 pull request 提交可复现问题与改进。请提供受影响的
skill、Codex 版本、预期行为、实际行为和最小可分享输入。示例应去除凭据、
私人科研数据和未公开的发明细节。

科研原则维护在 `skills/skills-codex/shared-references/evo-inquiry.md`。
保持原则简洁、可跨项目迁移；项目偏好放在项目自身说明中。
其他客户端包目前保留上游实现。

修改时保留流程的输出、恢复合同及授权范围。删除或合并入口前核对调用者。
`tools/skill-groups.tsv` 记录默认依赖，可选分支可能需要额外入口。
后端是否可用应依据实际检查，不能仅凭存在 skill 文件作出判断。

执行 README 中的检查，并在变更需要时补充有意义的行为测试。区分模拟测试、
本地集成、真实供应商检查和科研证据，记录尚未解决的限制。
安装方式的变化应附带跨平台 CI 结果。

公开文档聚焦安装、使用、兼容与维护。`tools/publication-policy.json` 明确列出
不随包发布的材料与必须保留的引用文件；修改时先检查调用方。集成上游变更时，
保留 LICENSE 与 NOTICE。贡献以 MIT 许可证分发。
