# WorkBuddy / CodeBuddy 工作流跳转

模式：`inline`。`/aegis:propose <name> --loop` 在当前主 Agent 中按 Router 返回值依次执行
`workflows/single/` 或 `workflows/workspace/` 下的唯一阶段正文。

- 已路由的内部阶段复用保留 feature、`execution_scope` 与 trigger，跳过重复入口路由。
- 每个阶段独立完成并写入真实证据；Apply 的双轴评审属于同一 Apply Stage，不创建独立 Review 阶段。
- 遇到需求决策、边界冲突或失败时暂停，不自动跳过；解决后用同名 `propose --loop` 续跑。
- 三阶段顺序固定为 Propose → Apply → Archive，不得由 Host Kit 改写。
