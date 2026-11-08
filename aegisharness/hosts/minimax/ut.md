# MiniMax Code 单测工作流

`/aegis:ut` 的物理入口为本文件，业务边界仍由 `commands/ut.md` 与
`reference/ut-business-protocol.md` 定义。

1. 扫描项目测试布局与可测包，向用户确认目标包与并发度。
2. 支持显式参数 `--packages <pkgs>` 与 `--concurrency <n>`；未提供时先扫描再询问。
3. 测试生成、执行与修复使用宿主原生终端工具，保留真实退出码。
4. 不把 `ut` 结果计为 Apply 的验证证据；Apply 的验证仍以 `verify-report.md` 为准。
5. 并发度受宿主子代理能力限制；超出时串行执行并说明。
