# 💊 HomeMeds Pro (家庭药箱助手)

**HomeMeds Pro** 是一个基于 **Streamlit** 构建的现代化家庭药品库存管理系统。它不仅能帮你记录家里的药还剩多少、有没有过期，更引入了 **"官方/用户数据隔离"** 机制，确保药品信息的准确性与安全性。同时，内置的 **AI 药剂师**（支持 DeepSeek/OpenAI）能基于你的库存提供智能用药建议。

> **当前版本**: v0.6 (模块化重构版)

## ✨ 核心功能

### 1. 🏥 智能库存管理

* **双模式操作**：
* **🥣 吃药打卡**：记录单次用量（如“吃2粒”），自动扣减库存。
* **📝 库存盘点**：直接修正剩余总量（如“还剩半瓶”），支持药膏/液体的模糊计量。


* **全景看板**：实时展示总库存、临期预警（90天内）及过期药品统计，过期药品高亮标红。

### 2. 🔍 极速入库流程

* **多维搜索**：支持 **扫码录入** 或 **药名模糊搜索**（如输入“感冒”自动匹配条码）。
* **专业字段**：收录 14 项核心信息，包括**适应症、禁忌、不良反应、孕妇/儿童/老年人特殊用药指南**。
* **位置管理**：记录药品存放位置（电视柜、冰箱等）及归属人。

### 3. 🛡️ 官方/用户数据隔离 (独家特性)
**HomeMeds Pro** 是一个基于 **Streamlit** 构建的现代化家庭药品库存管理系统。它不仅能帮你记录家里的药还剩多少、有没有过期，更引入了 **"官方/用户数据隔离"** 机制，确保药品信息的准确性与安全性。同时，内置的 **AI 药剂师**（支持 DeepSeek/OpenAI）能基于你的库存提供智能用药建议。

> **当前版本**: v0.6 (模块化重构版)

## ✨ 核心功能

### 1. 🏥 智能库存管理

* **双模式操作**：
* **🥣 吃药打卡**：记录单次用量（如“吃2粒”），自动扣减库存。
* **📝 库存盘点**：直接修正剩余总量（如“还剩半瓶”），支持药膏/液体的模糊计量。


* **全景看板**：实时展示总库存、临期预警（90天内）及过期药品统计，过期药品高亮标红。

### 2. 🔍 极速入库流程

* **多维搜索**：支持 **扫码录入** 或 **药名模糊搜索**（如输入“感冒”自动匹配条码）。
* **专业字段**：收录 14 项核心信息，包括**适应症、禁忌、不良反应、孕妇/儿童/老年人特殊用药指南**。
* **位置管理**：记录药品存放位置（电视柜、冰箱等）及归属人。

### 3. 🛡️ 官方/用户数据隔离 (独家特性)

* **权威优先**：引入 `is_standard` 机制。
* **官方数据**（🔒）：由维护者录入，包含完整的安全信息，普通用户只读，防止误改。
* **用户数据**（✏️）：用户可自由录入偏方或新药，灵活管理。
* **权威优先**：引入 `is_standard` 机制。
* **官方数据**（🔒）：由维护者录入，包含完整的安全信息，普通用户只读，防止误改。
* **用户数据**（✏️）：用户可自由录入偏方或新药，灵活管理。


* **种子同步**：支持将官方数据导出为 JSON 种子文件，通过 Git 分发，实现“一人维护，全员受益”。
* **种子同步**：支持将官方数据导出为 JSON 种子文件，通过 Git 分发，实现“一人维护，全员受益”。

### 4. 🤖 AI 私人药剂师 (RAG)
### 4. 🤖 AI 私人药剂师 (RAG)

* 基于 **DeepSeek-V3** 或 **OpenAI** 大模型。
* **上下文感知**：AI 能够读取你当前的库存清单。
* **安全护栏**：严格检查药品说明书中的【禁忌】与【儿童用药】字段，提供安全的用药建议。
* 基于 **DeepSeek-V3** 或 **OpenAI** 大模型。
* **上下文感知**：AI 能够读取你当前的库存清单。
* **安全护栏**：严格检查药品说明书中的【禁忌】与【儿童用药】字段，提供安全的用药建议。

---

## 🛠️ 技术架构 (v0.6)

本项目采用 **MVC 模式** 进行模块化重构，结构清晰，易于扩展。
## 🛠️ 技术架构 (v0.6)

本项目采用 **MVC 模式** 进行模块化重构，结构清晰，易于扩展。

```text
HomeMeds/
HomeMeds/
├── data/
│   ├── medicines.db          # SQLite 数据库 (本地存储，含库存)
│   └── catalog_seed.json     # 官方药品种子库 (JSON，Git版本控制)
│   ├── medicines.db          # SQLite 数据库 (本地存储，含库存)
│   └── catalog_seed.json     # 官方药品种子库 (JSON，Git版本控制)
├── src/
│   ├── database.py           # 数据库初始化、种子导入导出逻辑
│   ├── services/             # [业务逻辑层]
│   │   ├── catalog.py        # 公共药库增删改查
│   │   ├── inventory.py      # 库存操作核心
│   │   ├── queries.py        # 数据统计与联表查询
│   │   └── ai_service.py     # AI 上下文构建
│   └── views/                # [界面展示层]
│       ├── sidebar.py        # 侧边栏与全局设置
│       ├── dashboard.py      # 看板页面
│       ├── operations.py     # 核心操作页面
│       └── ai_doctor.py      # AI 聊天页面
├── app.py                    # 应用主入口
├── requirements.txt          # 依赖列表
└── README.md                 # 说明文档
│   ├── database.py           # 数据库初始化、种子导入导出逻辑
│   ├── services/             # [业务逻辑层]
│   │   ├── catalog.py        # 公共药库增删改查
│   │   ├── inventory.py      # 库存操作核心
│   │   ├── queries.py        # 数据统计与联表查询
│   │   └── ai_service.py     # AI 上下文构建
│   └── views/                # [界面展示层]
│       ├── sidebar.py        # 侧边栏与全局设置
│       ├── dashboard.py      # 看板页面
│       ├── operations.py     # 核心操作页面
│       └── ai_doctor.py      # AI 聊天页面
├── app.py                    # 应用主入口
├── requirements.txt          # 依赖列表
└── README.md                 # 说明文档

```

---

## 🚀 快速开始
## 🚀 快速开始

### 1. 环境准备

确保已安装 Python 3.8+。
### 1. 环境准备

确保已安装 Python 3.8+。

```bash
# 克隆项目
git clone https://github.com/your-username/HomeMeds.git
cd HomeMeds

# 创建虚拟环境 (推荐)
python -m venv .venv
# Windows 激活:
.venv\Scripts\activate
# Mac/Linux 激活:
source .venv/bin/activate

# 安装依赖
# 克隆项目
git clone https://github.com/your-username/HomeMeds.git
cd HomeMeds

# 创建虚拟环境 (推荐)
python -m venv .venv
# Windows 激活:
.venv\Scripts\activate
# Mac/Linux 激活:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

```

### 3. 配置 API Key

在根目录创建 `.env` 文件，填入你的 LLM API Key：

```ini
# .env 文件
LLM_API_KEY="sk-xxxxxxxxxxxxxxxx"
LLM_BASE_URL="https://api.deepseek.com/v1"  # 示例：使用 DeepSeek

```

### 4. 运行应用

```bash
streamlit run app.py

```

运行后，浏览器将自动打开 `http://localhost:8501`，手机连接同一 WiFi 即可访问。

---

## 📅 开发路线图 (Roadmap)

* [ ] **Phase 1:** 完成数据库建模与 Streamlit 录入/展示界面。
* [ ] **Phase 2:** 接入 LLM API，实现“基于库存的症状问答”。
* [ ] **Phase 3:** 引入 OCR 功能，上传药盒照片自动填表 (OpenCV/PaddleOCR)。
* [ ] **Phase 4:** 语音交互支持 (Whisper)。

---

## 🤝 贡献与协议

本项目仅供学习与家庭个人使用。
**免责声明：** AI 推荐仅供参考，不构成专业医疗建议。用药前请务必阅读纸质说明书或咨询医生。

License: MIT