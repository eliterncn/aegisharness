# DeepSeek Harness (dsh) 宿主运行时

本 Host Kit 只映射物理执行方式，不改变公共业务契约。逻辑动作映射如下：

| 逻辑动作 | DSH 行为 |
| --- | --- |
| `read_file` | 使用 Standard/Code preset 的原生只读文件工具读取确定路径 |
| `edit_file` | 使用 `str_replace_editor` 或等价原生编辑工具，保留写域与单写者约束 |
| `run_command` | 使用 DSH 的持久 `bash` 工具，保留真实退出码与标准输出 |
| `invoke_skill` | 使用 DSH 原生 Skill 发现机制；`invoke_skill(name)` 映射为 `/aegis-{name}` |
| `spawn_job` | 按 `hosts/deepseek-dsh/subagent.md` 派发子代理或等价只读子任务 |
| `wait_job` | 等待已派发任务的真实终态并校验返回身份与产物 |
| `ask_user` | 使用普通文本提问并等待真实回答；需求决策不使用结构化弹窗 |
| `update_plan` | 使用 DSH 的 plan/goal 或 todo 工具；不可用时更新当前 Feature 的 `tasks.md` |
| `stage_finish` | 由公共命令显式记账，不依赖宿主 Stop hook |
| `project_entry` | 生成或合并项目根 `AGENTS.md` |
| `project_hooks` | 声明为 `unsupported`：不写宿主设置文件，检查由 `docs/hooks/` 清单显式驱动 |

DSH 的 Session/Trajectory 是 append-only 事件流，可用于人工核对证据，但**不是**本插件的
遥测账本。不得凭宿主名称猜测能力，也不得借用其他 Host Kit 的环境变量、缓存或入口脚本。
遥测能力为 `unsupported`：不启动 Runtime、不写同步账本、不投递异步数据。

需要确认 profile 组合后的实际配置时使用 `npx @deepseek-ai/dsh --profile web --dump-config`；
headless 场景使用 `npx @deepseek-ai/dsh --profile headless "<task>"`。
