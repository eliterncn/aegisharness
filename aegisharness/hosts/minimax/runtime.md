# MiniMax Code 宿主运行时

本 Host Kit 只映射物理执行方式，不改变公共业务契约。逻辑动作映射如下：

| 逻辑动作 | MiniMax Code 行为 |
|---|---|
| `read_file` | 使用宿主原生只读文件工具读取确定路径 |
| `edit_file` | 使用宿主原生编辑工具，保留写域与单写者约束 |
| `run_command` | 使用宿主原生终端工具，保留真实退出码与标准输出 |
| `invoke_skill` | 使用原生 Skill 发现机制；`invoke_skill(name)` 映射为 `/aegis:{name}` |
| `spawn_job` | 按 `hosts/minimax/subagent.md` 派发子代理或等价只读子任务 |
| `wait_job` | 等待已派发任务的真实终态并校验返回身份与产物 |
| `ask_user` | 使用普通文本提问并等待真实回答；需求决策不使用结构化弹窗 |
| `update_plan` | 使用宿主任务/计划工具；不可用时更新当前 Feature 的 `tasks.md` |
| `stage_finish` | 由公共命令显式记账，不依赖宿主 Stop hook |
| `project_entry` | 生成或合并 `AGENTS.md` |
| `project_hooks` | 声明为 `unsupported`：不写宿主设置文件，检查由 `docs/hooks/` 清单显式驱动 |

不得凭宿主名称猜测能力，也不得借用其他 Host Kit 的环境变量、缓存或入口脚本。
遥测能力为 `unsupported`：不启动 Runtime、不写同步账本、不投递异步数据。
