# 📚 作业搭子 (Homework Pal)

AI-powered homework assistant for 3rd grade students using 人教版 (PEP) textbooks with advanced RAG capabilities.

## 🎯 项目概述

**核心定位**: 基于 Chainlit 框架的、专为使用**人教版教材**的三年级学生设计的智能作业辅导 Agent

**技术栈**:
- **后端**: PostgreSQL + timescale-vector + LangChain + FastAPI
- **前端**: Chainlit (交互式Web界面)
- **AI引擎**: 国产 LLM (Qwen/DeepSeek) + BGE-M3 向量模型
- **部署**: Uvicorn + Docker (可选)

**核心价值**:
1. **精准辅导**: 基于人教版教材的 RAG，提供书本级的知识点溯源
2. **闭环学习**: 从作业检查到错题归档，形成完整的学习闭环
3. **情绪价值**: 以鼓励为主的交互风格，保护孩子的学习兴趣

## 🛠️ 系统要求

### 基础环境

- **Python**: 3.11+
- **PostgreSQL**: 14+ with pgvector extension
- **UV**: Python 包管理器 ([安装指南](https://docs.astral.sh/uv/))
- **操作系统**: macOS / Linux / Windows (WSL2)

## 🚀 快速开始

### 方法1：简化版测试（推荐新手）

自动启动服务、测试功能、然后停止服务：

```bash
./scripts/test_complete.sh
```

### 方法2：手动启动和测试

1. 启动服务：
```bash
./scripts/start_services.sh
```

2. 在另一个终端运行测试：
```bash
./scripts/test_simple.sh
```

### 方法3：直接使用Python模块

```bash
# 启动后端
python -m homeworkpal.simple.api

# 启动前端
chainlit run homeworkpal.simple.app --host 0.0.0.0 --port 8000

# 或使用入口脚本
python run_simple_api.py
```

### 方法4：完整环境初始化

```bash
./init.sh
```

## 🌐 服务访问地址

> **📝 重要说明**：
> - 服务器启动时显示 `0.0.0.0` 表示监听所有网络接口
> - 但在浏览器中访问时，请使用 `localhost` 或 `127.0.0.1`
> - `localhost:8000` 是浏览器访问的正确地址

### 简化版服务
- **前端界面**: http://localhost:8000
- **后端API**: http://localhost:8001
- **API文档**: http://localhost:8001/docs

### 完整版服务（需要完整初始化）
- **前端界面**: http://localhost:8000
- **后端API**: http://localhost:8001
- **API文档**: http://localhost:8001/docs

## 📁 项目结构

```
homeworkpal/
├── pyproject.toml           # 项目配置和依赖
├── README.md               # 项目文档
├── init.sh                 # 环境初始化脚本
├── run_simple_api.py       # 简化版API入口
├──
├── homeworkpal/            # 主包目录
│   ├── core/               # 核心业务逻辑
│   ├── api/                # FastAPI后端
│   ├── frontend/           # Chainlit前端
│   ├── simple/             # 简化版服务
│   ├── database/           # 数据库相关
│   ├── llm/               # LLM集成
│   ├── vision/            # 图像处理
│   └── utils/             # 工具函数
│
├── scripts/               # 脚本目录
├── tests/                 # 测试目录
├── docs/                  # 文档目录
└── data/                  # 数据目录
```

> 📋 **详细结构说明**：参见 [docs/项目结构.md](docs/项目结构.md)

## 🧪 测试指南

### 简化版测试结果

✅ **后端API测试**
- 根端点 (`/`) - 返回欢迎消息
- 健康检查 (`/health`) - 服务状态检查
- 状态API (`/api/v1/status`) - 系统状态信息

✅ **前端界面测试**
- 页面可访问性检查
- 基本交互功能

### 手动测试指南

启动服务后，你可以：

1. **访问前端界面**
   - 打开 http://localhost:8000
   - 与聊天机器人"小栗子"对话
   - 测试功能按钮

2. **测试后端API**
   - 访问 http://localhost:8001/docs 查看API文档
   - 直接测试各个端点

3. **查看日志**
   - 后端日志：`backend.log`
   - 前端日志：`frontend.log`

## 🛠 故障排除

### 端口冲突
如果遇到端口被占用的问题：
```bash
# 查看占用端口的进程
lsof -i :8000  # 前端端口
lsof -i :8001  # 后端端口

# 停止进程
kill -9 <PID>
```

### 依赖问题
确保虚拟环境已正确设置：
```bash
# 重新初始化环境
./init.sh

# 手动安装依赖
source .venv/bin/activate
pip install chainlit fastapi uvicorn
```

### 服务无法启动
1. 检查Python版本（需要>=3.11）
2. 确保虚拟环境激活
3. 查看错误日志文件

## 🔍 验证成功标志

当你看到以下输出时，表示基本功能测试通过：

```
🎉 All tests passed successfully!

✅ Root endpoint working
✅ Health endpoint working
✅ Status API working
✅ Frontend responding
```

这证明了项目的基础架构已经正确配置，可以继续开发更高级的功能。

## 📝 下一步

简化版验证通过后，你可以：
1. 运行 `./init.sh` 设置完整的开发环境
2. 按照项目文档添加RAG功能
3. 集成数据库和AI模型

## 📚 更多文档

- [docs/项目结构.md](docs/项目结构.md) - 详细的项目架构说明
- [docs/开发任务分拆.md](docs/开发任务分拆.md) - 开发任务分解
- [docs/环境配置指南.md](docs/环境配置指南.md) - 环境配置详情
- [docs/作业搭子产品文档.md](docs/作业搭子产品文档.md) - 产品设计文档

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。