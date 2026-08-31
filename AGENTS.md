# AI in the Wild

## 项目简介

AI in the Wild 是一个将人工智能、野外传感器和边缘计算应用于野生动物研究与保护的开源计划。第一阶段重点是建立文档驱动、项目驱动的开源研究体系，而不是立即沉淀重模型代码。

## 技术栈

- 文档：Markdown
- 数据规范：JSON Schema
- 协作平台：GitHub Issues / Pull Requests / Actions
- 未来可能扩展：Python、边缘 AI、计算机视觉、生物声学、时间序列分析、LLM 辅助研究分析

## 目录结构

- `docs/`：愿景、架构、野外部署、数据治理、研究主题、硬件和 AI 能力说明
- `projects/`：项目入口、项目模板和后续示例
- `reference-implementations/`：未来参考实现占位
- `schemas/`：通用野外研究数据 JSON Schema
- `.github/`：Issue 模板、PR 模板和文档检查
- `docs/sessions/`：跨会话日志

## 当前状态

### 活跃分支

| 分支 | 任务 |
|---|---|
| `dev` | 完善首页对 reCamera Pro + Meshtastic 链路验证 demo 的展示入口，以及 demo 案例页、图片素材和参考实现代码 |

### 已完成功能

- 第一版开源研究体系仓库骨架：双语 README、治理文档、六个研究主题、项目模板、JSON Schema、GitHub 协作模板和基础检查工作流。
- `dev` 分支新增第一个试点 demo：用公司野猫作为代理目标，验证 reCamera Pro 边缘识别、GPIO 触发、Meshtastic 告警和 Wio Tracker L1 Pro 接收链路；首页展示真实接收告警图和入口链接，案例页包含设备购买链接、实拍图、Meshtastic 配置截图、运行报告和参考实现代码入口。

## 重要约定

- 第一阶段以文档、模板、数据规范和项目治理为主，避免过早加入重模型代码。
- 新研究项目应先使用 `projects/project-template/` 或 GitHub project proposal issue 描述清楚。
- 物种位置、繁殖点、濒危动物、未公开数据等信息默认按敏感数据处理。
- Reference implementations 只有在真实项目验证后再加入。

## 变更日志

| 日期 | 分支 | 说明 |
|---|---|---|
| 2026-07-17 | `feature/initial-open-framework` | 初始化开源研究体系仓库骨架 |
| 2026-07-17 | `main` | 合并第一版开源研究体系仓库骨架 |
| 2026-08-31 | `dev` | 新增 reCamera Pro + Meshtastic 链路验证 demo 的项目页和参考实现入口 |
| 2026-08-31 | `dev` | 完善链路验证 demo 为可复现案例页，补充图片、购买链接、配置说明和参考实现代码目录 |
| 2026-08-31 | `dev` | 在中英文首页增加 Featured Pilot Demo 图片入口和完整 demo/参考实现链接 |
