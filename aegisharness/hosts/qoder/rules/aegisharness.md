# AegisHarness 工程规则（Qoder）

- 所有研发任务通过 `/aegis:*` 公共命令进入，先加载 `docs/harness/index.md` 与 `docs/knowledge/index.md`。
- 不跳过索引凭路径猜测读取未索引文件；`docs/specs/**` 与 `docs/hooks/**` 由命令直接指定。
- Spec、Tasks 与 `verify-report.md` 是完成证据，缺失时不得声称完成或归档。
- Apply 必须包含测试与双轴评审；审查后内容变更需重新评审。
- 不改写 Propose → Apply → Archive 的顺序、产物或门禁。
- Quest 模式生成的 Spec 不能替代 AegisHarness 的 Spec/Tasks 契约，两者并行时以本插件契约为准。
