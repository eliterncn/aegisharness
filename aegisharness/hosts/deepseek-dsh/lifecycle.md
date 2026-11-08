# DeepSeek Harness (dsh) 生命周期适配

- 不注册插件级 SessionStart / SessionEnd / Stop / Failure hook；本宿主相关能力声明为 `unsupported`。
- 阶段开始、完成与失败由公共命令通过 `scripts/metrics.py` 显式记账（遥测关闭时只跳过采集，不跳过业务闸门）。
- 项目级 hooks 声明为 `unsupported`：Init 不创建宿主设置文件，也不合并 JSON hook。
- 质量检查通过 `docs/hooks/` 清单与公共命令中的检查点显式执行，不由宿主事件自动触发。
- 安装或更新 skills 后必须重启 `dsh web` / `dsh --profile ...` 并新开会话；DSH 的会话是
  append-only 事件流，旧会话不会自动装载新增 Skill。
- 通过 `python3 scripts/host_runtime_cli.py resolve --platform deepseek-dsh` 确认 Host Context 绑定正确。
- 统计关闭不改变工作流完成门禁；不支持的能力一律关闭失败，不回退到其他宿主。
