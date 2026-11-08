# Host Kit 骨架模板

复制本目录到 `../../aegisharness/hosts/{host-id}/`，把 `HOST_ID` 等占位符替换为真实值，
再按 [新增宿主接入规范](../add-new-host.md) 补齐其余资源文件。

> 本模板放在 `docs/` 下是刻意的：Registry 只扫描 `hosts/*/host.json`，
> 模板不会被当成已安装宿主载入。**不要把 `host.json` 放进 hosts 目录以外的其他位置**
> 后又在 hosts 下留一份未完成的清单，否则 `list` 会整体关闭失败。

## 占位符

| 占位符 | 说明 | 示例 |
| --- | --- | --- |
| `HOST_ID` | kebab-case 宿主 ID，须与目录名一致、全局唯一 | `cursor` |
| `DISPLAY_NAME` | 展示名 | `Cursor` |
| `ALIAS_1` | 可选输入别名（可删空数组） | `cursor-cli` |
| `ENTRY_FILE` | 项目指令文件 | `AGENTS.md` |
| `MANIFEST_PATH` | 原生分发清单路径 | `.cursor-plugin/plugin.json` |
| `DETECTOR` | detector 函数名 | `detect_cursor` |

## 需要补齐的文件

模板只提供四个 JSON 契约骨架。以下 Markdown 资源必须自行撰写（Registry 会校验文件存在）：

`installer.md`、`runtime.md`、`subagent.md`、`workflow-transition.md`、`ut.md`、
`lifecycle.md`；以及按 `surface` 决定的九个命令入口：

- `native-command`：可直接复用共享 `commands/*.md`（把投影入口指向它们）。
- `skill`：为每个命令写 `skills/{command}/SKILL.md` 薄入口，正文明确完整读取
  `commands/{command}.md`，不复制业务正文。

另需在插件根与仓库根创建 `MANIFEST_PATH` 指向的原生分发清单。

## 复制后立刻验证

```bash
cd aegisharness/aegisharness/scripts
python3 host_runtime_cli.py list
python3 host_runtime_cli.py resolve --platform HOST_ID
python3 run_tests.py
```
