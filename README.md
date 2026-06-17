<div align="center">

# 🤖 AIGC 检测器

<i>🕵️ 让英雄去查英雄，让好汉去查好汉</i>

![License](https://img.shields.io/badge/license-AGPL--3.0-green?style=flat-square)
![Python](https://img.shields.io/badge/python-3.10+-blue?style=flat-square&logo=python&logoColor=white)
![AstrBot](https://img.shields.io/badge/framework-AstrBot-ff6b6b?style=flat-square)

</div>

## 📖 简介

一款为 [AstrBot](https://github.com/AstrBotDevs/AstrBot) 设计的 AIGC 内容检测插件，利用多模态 LLM 对图片进行多维分析，判断图片是否为 AI 生成，并以图文报告的形式展示检测结果。

> [!CAUTION]
> 本插件基于 LLM 视觉能力进行判断，更多是**娱乐**性质，实际效果有限。鉴定结果可以作为与你自身判断相合时的佐证，但相左时**不必盲信**。

---

## ✨ 功能特性

* **多维检测**：调用多模态 LLM，从光影物理、生物细节、图层结构、像素排版、线条幻觉等维度综合分析。
* **图文报告**：自动生成图文报告，含缩略图、卡片分析、AI 程度评分。
* **四级判定**：AI 生成（90-100）、疑似 AI 生成（65-89）、无法确定（40-64）、非 AI 生成（0-39），并列出核心依据。

---

## 💿 安装

1. **安装插件**：下载本插件的完整文件夹，并放入 AstrBot 的 `data/plugins/` 目录下。

2. **重启 AstrBot**。

---

## ⚙️ 配置

首次加载后，请在 AstrBot 后台 -> 插件 页面找到本插件进行设置。

| 配置项 | 说明 |
| :--- | :--- |
| 图像鉴定模型 | 选择一个支持多模态的 LLM 提供商用于图像鉴定。留空表示使用当前会话默认模型。 |
| 图像鉴定提示词 | 作为 system prompt 发送给 LLM，用于引导图像鉴定的判断标准与输出格式。 |

> [!IMPORTANT]
> 修改鉴定提示词时请勿移除 JSON 输出约束，否则可能导致解析失败。

> [!TIP]
> 鉴于 AI 绘画日益强大，建议使用前沿模型（如 Gemini 3.5 Flash）以获得更准确的鉴定结果。

---

## 📖 使用指南

### 📋 指令列表

| 指令 | 作用 |
| :--- | :--- |
| `鉴定` | 分析当前图片（需附带图片，或回复包含图片的消息） |

### 💡 使用方法

发送一张图片并在消息中包含 `鉴定` 指令：

```
鉴定
```

也可以附带说明：

```
鉴定 这张图看起来像 AI 画的吗
```

插件会自动下载图片，调用 LLM 进行分析，并返回一张图文检测报告。

---

## 📝 更新日志

详见 [CHANGELOG](CHANGELOG.md)

---

## ❤️ 支持

* [AstrBot 帮助文档](https://astrbot.app)
* 如果您在使用中遇到问题，欢迎在本仓库提交 [Issue](https://github.com/Foolllll-J/astrbot_plugin_aigc_detector/issues)。

---

<div align="center">

**如果本插件对你有帮助，欢迎点个 ⭐ Star 支持一下！**

</div>
