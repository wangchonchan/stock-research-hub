# 🚀 Stock Research Hub

**一个智能股票分析平台，可以自动进行深度调研并生成动态更新的分析报告。**

## 💡 核心理念

传统的股票分析报告是**静态的、过时的**。而这个项目实现了**动态的、实时更新的**自动化研究系统：

- ✅ **自动调研** - 一键启动深度调研流程
- ✅ **动态生成** - 根据最新数据自动生成网页
- ✅ **本地存储** - 所有代码和数据在您的电脑/GitHub 上
- ✅ **可扩展** - 轻松添加新的数据源和分析逻辑

## 🎯 快速开始

### 1. 生成初始报告

```bash
cd /home/ubuntu/stock_research_hub
python3 research_engine.py FIGR
python3 generate_html.py
```

### 2. 查看报告

在浏览器中打开 `index.html` 文件。

### 3. 更新报告

```bash
./update.sh FIGR
```

## 📊 工作流程

```
调研脚本 (research_engine.py)
    ↓
    抓取数据 → 保存为 JSON
    ↓
生成脚本 (generate_html.py)
    ↓
    读取 JSON → 生成 HTML
    ↓
网页 (index.html)
    ↓
在浏览器中查看
```

## 📁 项目文件

| 文件 | 说明 |
|------|------|
| `research_engine.py` | 深度调研脚本，抓取股票数据 |
| `generate_html.py` | HTML 生成脚本，根据数据生成网页 |
| `update.sh` | 自动化脚本，一键执行调研和生成 |
| `research_data_FIGR.json` | 调研数据（自动生成） |
| `index.html` | 生成的网页（自动生成） |
| `RESEARCH_SYSTEM.md` | 详细文档 |

## 🔧 自定义

### 修改分析的股票

```bash
./update.sh AAPL
./update.sh TSLA
```

### 添加新的数据源

编辑 `research_engine.py`，添加新的方法（例如 `fetch_news_sentiment()`）。

### 修改网页样式

编辑 `generate_html.py` 中的 HTML 和 CSS。

## 📚 详细文档

查看 `RESEARCH_SYSTEM.md` 了解更多信息。

## 🚀 部署到 GitHub

```bash
git add .
git commit -m "Initial commit: Stock Research Hub"
git branch -M main
git remote add origin https://github.com/wangchonchan/stock-research-hub.git
git push -u origin main
```

## 💻 系统要求

- Python 3.7+
- Bash（macOS/Linux）或 PowerShell（Windows）

## 📞 支持

有问题？查看 `RESEARCH_SYSTEM.md` 中的故障排除部分。

---

**版本：** 1.0.0  
**最后更新：** 2026-04-16  
**作者：** Manus AI
