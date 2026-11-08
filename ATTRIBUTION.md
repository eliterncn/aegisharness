# Attribution / 上游来源声明

AegisHarness 是公司内部标准研发工具，派生自以下 Apache-2.0 开源项目：

| 项目 | 上游仓库 | 许可证 |
| --- | --- | --- |
| HelixHarness 1.0.0 | https://github.com/didi/helixharness | Apache License 2.0 |

## 改动说明

在本公司内部发行版中：

- 产品与插件标识统一改为 **AegisHarness / aegisharness / `aegis`**（命令命名空间 `/aegis:*`）；
- 新增 MiniMax Code、WorkBuddy / CodeBuddy、Qoder 等宿主支持，并把宿主支持矩阵改为清单驱动；
- 新增公司级接入规范、宿主模板与验证脚本；
- 调整 README、安装与使用文档以匹配公司研发流程。

## 图片资产处理

上游 `docs/assets/platform-*.png` 三张平台界面截图与
`aegisharness-platform/web_ui/static/images/evolution-evidence-loop.png` 内嵌有上游品牌文字。
公司发行版不再引用这些截图：README 的三个平台视图改为文字说明；自进化证据闭环图已重绘为
`evolution-evidence-loop.svg`（AegisHarness 品牌），模板与测试同步指向 SVG。

含品牌文字的 5 个 PNG 已全部删除（清单如下，仅作历史记录）：

```
docs/assets/platform-demo.png
docs/assets/platform-evaluation.png
docs/assets/platform-evolution.png
docs/assets/platform-observability.png
aegisharness-platform/web_ui/static/images/evolution-evidence-loop.png
```

`docs/assets/readme-*.png` 与 `readme-*.svg` 为无品牌文字的通用流程图，予以保留。

## 保留的声明

依据 Apache License 2.0 第 4 条（尤其是 4(c) 与 4(d)），上游作品中的版权、专利、商标与归属声明必须原样保留。因此：

- 各 `NOTICE` 文件中保留上游版权行 `Copyright 2026 DiDi Financial and HelixHarness contributors`；
- `LICENSE` 保持 Apache-2.0 全文不变；
- `THIRD_PARTY_NOTICES.md` 及其子文件保留第三方组件（OpenSpec、superpowers、mattpocock/skills、HTMX、Tailwind CSS 等）的原始许可证文本。

这些文件中出现的上游名称属于**法律归属声明**，不是本产品的品牌标识。产品代码、命令、配置、文档与运行时标识中不再使用上游品牌。

> **署名状态**：`NOTICE`（4 份）中的版权人已填为 `elierncn`，与上游版权行并列保留；
> 文档与 `pyproject.toml` 中的仓库地址已统一为 `github.com/elierncn/aegisharness`。
> 仓库正式公开后，README 与安装文档里的克隆/PowerShell 命令即可直接使用。
