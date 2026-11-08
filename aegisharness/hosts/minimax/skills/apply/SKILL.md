---
name: apply
description: "执行任务、验证并完成双轴代码评审。"
triggers:
  - /aegis:apply
---

插件根为当前文件的 `../../../..`。先完整读取 `hosts/minimax/skill-entry.md`，
再完整读取唯一公共命令契约 `commands/apply.md`，并按该契约执行。

- `$ARGUMENTS` 按 shell token 解析；flag 精确匹配，不做子串推断。
- 不改写工作流顺序、产物、门禁或完成条件；不读取其他宿主的入口或运行时文件。
- 需要的项目约束、知识、Spec/Tasks 与验证证据，按 `reference/loading-protocol.md` 的索引加载。
- 指标与遥测在本宿主声明为 `unsupported`：不采集、不投递、不伪造账本。
