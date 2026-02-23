# AI 智能旅行助手

基于HelloAgent（https://github.com/datawhalechina/hello-agents）的学习，对后端代码进行了重构和优化，并提供将景点名称、地名等翻译成英文，以便更好的匹配图片的搜索。前端代码微调。

基于 AI 的个性化旅行规划助手，利用多智能体系统提供完整的旅行计划解决方案。

## 🌟 项目简介

智能旅行助手是一个结合人工智能技术和高德地图 API 的旅行规划平台。它使用多智能体协作系统，能够根据用户的偏好自动生成详细的旅行计划，包括景点推荐、餐饮安排、住宿建议、交通规划和预算估算等。

## 🚀 核心特性

- **AI 驱动**: 使用大型语言模型（LLM）进行智能规划
- **多智能体协作**: 不同专业领域的智能体协同工作
- **实时数据**: 整合高德地图 API 获取最新景点和天气信息
- **可视化地图**: 集成高德地图展示景点位置和路线
- **灵活定制**: 支持多种旅行偏好设置和个性化要求
- **多媒体输出**: 支持行程计划导出为图片或 PDF

## 🛠 技术栈

### 后端
- **Python**: 主要开发语言
- **FastAPI**: Web 框架，支持异步处理和自动 API 文档
- **Pydantic**: 数据验证和序列化
- **MCP**: Map Compatible Protocol，用于集成地图服务

### 前端
- **Vue 3**: 前端框架
- **TypeScript**: 类型安全
- **Ant Design Vue**: UI 组件库
- **高德地图 JS API**: 地图展示和交互
- **Vite**: 构建工具

## 🏗 项目结构

```
travel-assistant/
├── backend/
│   ├── app/
│   │   ├── agents/           # 智能体实现
│   │   │   └── trip_planner_agent.py  # 多智能体旅行规划系统
│   │   ├── api/
│   │   │   ├── routes/       # API 路由
│   │   │   │   ├── trip.py   # 旅行规划路由
│   │   │   │   ├── poi.py    # POI 搜索路由
│   │   │   │   └── map.py    # 地图相关路由
│   │   │   └── main.py       # 主应用入口
│   │   ├── models/           # 数据模型
│   │   │   ├── model.py      # Pydantic 模型定义
│   │   │   └── schemas.py    # 数据结构定义
│   │   ├── services/         # 服务层
│   │   │   ├── amap_service.py     # 高德地图服务
│   │   │   ├── llm_service.py      # LLM 服务
│   │   │   ├── unsplash_service.py # Unsplash 图片服务
│   │   │   └── pexels_service.py   # Pexels 图片服务
│   │   ├── tools/            # 工具层
│   │   │   ├── agents/       # 智能体相关工具
│   │   │   ├── llm/          # LLM 相关工具
│   │   │   ├── mcp/          # MCP 协议工具
│   │   │   ├── utils/        # 实用工具
│   │   │   │   └── chinese_to_english_translator.py  # 中英翻译工具
│   │   │   ├── base.py       # 基础工具类
│   │   │   └── registry.py   # 工具注册表
│   │   ├── config.py         # 配置管理
│   │   └── __init__.py
│   └── run.py                # 后端启动脚本
└── frontend/
    ├── src/
    │   ├── views/
    │   │   ├── Home.vue      # 主页组件
    │   │   └── Result.vue    # 结果页面组件
    │   ├── services/
    │   │   └── api.ts        # API 服务
    │   ├── types/
    │   │   └── index.ts      # 类型定义
    │   ├── App.vue           # 根组件
    │   └── main.ts           # 前端启动脚本
    ├── package.json          # 前端依赖
    └── vite.config.ts        # Vite 配置
```

## 🚀 快速开始

### 环境准备

1. **Python 3.9+** (后端)
2. **Node.js 18+** (前端)
3. **API 密钥**:
   - 高德地图 API Key
   - OpenAI 或其他 LLM API Key

### 后端安装

1. 进入后端目录
```bash
cd backend
```

2. 创建虚拟环境
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件,填入你的API密钥
```

5. 启动后端服务
```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

服务将在 `http://localhost:8000` 上运行，默认端口为 8000。

### 前端安装

1. 进入前端目录
```bash
cd frontend
```

2. 安装依赖
```bash
npm install
```

3. 配置环境变量
```bash
# 创建.env文件, 填入高德地图Web API Key 和 Web端JS API Key
cp .env.example .env
```

4. 启动开发服务器
```bash
npm run dev
```

5. 打开浏览器访问 `http://localhost:5173`

## 🧠 多智能体系统

### 智能体角色

1. **景点搜索专家** (`attraction_agent`): 负责搜索符合用户偏好的景点
2. **天气查询专家** (`weather_agent`): 提供目的地天气预报
3. **酒店推荐专家** (`hotel_agent`): 推荐合适的住宿地点
4. **行程规划专家** (`planner_agent`): 综合所有信息生成完整行程



## 🛠 实用工具

### 中英翻译工具

位于 [backend/app/tools/utils/chinese_to_english_translator.py](file:///d:/code/travel-assistant/github/travel-assistant/backend/app/tools/utils/chinese_to_english_translator.py)，提供以下功能：

- **百度翻译API**: 使用百度翻译服务进行高质量翻译
- **LLM翻译**: 当API不可用时，使用大语言模型作为备选方案
- **专有名词处理**: 对地名、景点名称等使用国际通用标准译名
- **批量翻译**: 支持一次翻译多个文本

该工具主要用于将中文景点名称、地名等翻译成英文，便于国际化展示和API调用。

