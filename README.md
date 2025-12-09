# 📚 作业搭子 (Homework Pal) RAG System

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

### 快速开始

```bash
# 克隆项目仓库
git clone <repository-url>
cd homeworkpal

# 1. 创建环境配置文件
cp .env.template .env

# 2. 编辑配置文件，填入你的API密钥
# 必需: DASHSCOPE_API_KEY 或 DEEPSEEK_API_KEY
nano .env  # 或使用你喜欢的编辑器

# 3. 一键初始化环境 (推荐)
./init.sh

# 4. 访问应用程序
# 前端界面: http://localhost:8000
# 后端API: http://localhost:8001
# API文档: http://localhost:8001/docs
```

### 环境配置

详细的配置指南请参考 [docs/环境配置指南.md](docs/环境配置指南.md)

**必需配置项**:
```bash
# 至少配置一个AI模型API密钥
DASHSCOPE_API_KEY=your_dashscope_api_key_here  # 阿里云通义千问
DEEPSEEK_API_KEY=your_deepseek_api_key_here    # DeepSeek模型

# 数据库连接（init.sh会自动配置PostgreSQL容器）
DATABASE_URL=postgresql://homeworkpal:password@localhost:5432/homeworkpal
```

**手动安装/开发**:
```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv sync

# 启动前端界面 (Chainlit)
chainlit run app.py --host 0.0.0.0 --port 8000

# 启动后端API (FastAPI) - 可选后台服务
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 服务地址

- **前端界面 (浏览器)**: http://localhost:8000
- **后端API**: http://localhost:8001
- **API文档**: http://localhost:8001/docs

> **💡 访问提示**：虽然服务器使用 `0.0.0.0` 启动（监听所有接口），但在浏览器中请使用 `localhost` 或 `127.0.0.1` 访问

## ⚙️ 配置说明

### 环境变量配置

创建 `.env` 文件并配置以下变量：

```bash
# 数据库配置
DATABASE_URL=postgresql://homeworkpal:password@localhost:5432/homeworkpal
DB_HOST=localhost
DB_PORT=5432
DB_NAME=homeworkpal
DB_USER=homeworkpal
DB_PASSWORD=password

# LLM API配置 (至少配置一个)
OPENAI_API_KEY=your_openai_api_key_here          # OpenAI (可选)
DASHSCOPE_API_KEY=your_dashscope_api_key_here    # 阿里云通义千问
DEEPSEEK_API_KEY=your_deepseek_api_key_here      # DeepSeek

# 向量数据库配置
VECTOR_DIMENSION=1536
EMBEDDING_MODEL=BAAI/bge-m3

# Chainlit配置
CHAINLIT_HOST=0.0.0.0
CHAINLIT_PORT=8000
```

### 初始化脚本选项

```bash
# 标准初始化
./init.sh

# 仅启动后端服务 (无前端)
./init.sh --no-frontend

# 重置向量数据库 (清空所有数据)
./init.sh --reset-vectordb

# 使用指定配置文件
./init.sh --env .env.production

# 批量导入教材文档
./init.sh --load-docs ./textbooks

# 查看所有选项
./init.sh --help
```

## 🏗️ 系统架构

### 1. 知识库模块 (RAG核心)
- **数据源**: 人教版三年级教材 (语文、数学、英语)
- **文档处理**: 按单元-课题-知识点进行层级切分
- **向量化**: BGE-M3 模型生成向量嵌入
- **检索**: 混合搜索 (关键词 BM25 + 向量语义搜索)
- **溯源**: 回答必须标注教材出处和页码

### 2. 视觉批改模块 (VLM)
- **图片输入**: 支持单张/多张作业图片上传
- **识别分析**: VLM 模型识别手写文字和题目内容
- **智能批改**: 基于教学理念的启发式引导
- **关联知识点**: 自动关联 RAG 检索到的课本内容

### 3. 错题本模块
- **自动记录**: 批改发现的错题自动存档
- **智能分类**: 按知识点和难度自动分类
- **互动复习**: "我学会了" 确认机制
- **导出功能**: 生成 PDF 格式的错题集

### 4. 作业清单模块
- **智能解析**: 家长转发的作业通知解析
- **任务分解**: Markdown 格式的结构化清单
- **进度同步**: 实时更新完成状态和进度条

## 📁 项目结构

```
homeworkpal/
├── app.py                 # Chainlit 前端界面
├── main.py               # FastAPI 后端服务
├── init.sh              # 一键初始化脚本
├── pyproject.toml       # Python 依赖配置
├── feature_list.json    # 功能测试清单
├── claude-progress.txt  # 会话进度记录
├── .env                 # 环境变量配置
├── .gitignore          # Git 忽略文件
├── README.md           # 项目说明文档
├── docs/               # 产品文档和设计文档
├── src/                # 核心源代码
│   ├── core/           # 核心业务逻辑
│   ├── database/       # 数据库操作
│   ├── llm/           # LLM 接口封装
│   ├── vision/        # 图像识别处理
│   └── utils/         # 工具函数
├── tests/             # 测试用例
├── data/              # 数据存储
│   ├── textbooks/     # 教材数据
│   └── user_generated/ # 用户生成数据
└── uploads/           # 文件上传目录
```

## 🎯 功能测试清单

### 核心功能测试

项目包含 35 项详细功能测试，覆盖 8 个核心模块：

1. **文档处理** (5项功能): PDF 解析、文本切分、向量化存储
2. **检索功能** (5项功能): 关键词检索、语义检索、混合搜索
3. **生成功能** (5项功能): 回答生成、质量验证、引用标注
4. **视觉功能** (3项功能): 作业批改、手写识别、教学反馈
5. **错题本** (4项功能): 错题记录、界面展示、进度跟踪、报告生成
6. **作业规划** (2项功能): 清单创建、进度同步
7. **用户界面** (5项功能): 文档管理、查询界面、结果展示
8. **性能监控** (5项功能): 系统监控、性能优化、质量评估

详细功能清单请查看: `feature_list.json`

### 开发测试

```bash
# 安装开发依赖
uv sync --dev

# 运行全部测试
pytest

# 运行特定模块测试
pytest tests/test_document_processing.py
pytest tests/test_vision_grading.py

# 运行覆盖率测试
pytest --cov=src tests/

# 代码格式检查
ruff check src/
black src/
```

### 健康检查

```bash
# 检查后端API健康状态
curl http://localhost:8001/health

# 检查前端界面状态
curl http://localhost:8000

# 检查系统状态
curl http://localhost:8001/api/v1/status
```

## 🚀 开发路线图

### Phase 1: 基础架构 (Day 1-2) ✅ 已完成
- [x] 搭建 PostgreSQL + pgvector
- [x] 配置 Chainlit 基础界面
- [x] 接入国产 LLM API
- [x] 建立项目开发规范

### Phase 2: 知识库构建 (Day 3-4) 🚧 进行中
- [ ] 处理人教版教材数据
- [ ] 实现 RAG 检索链路
- [ ] 优化向量化和切分算法
- [ ] 测试检索准确率

### Phase 3: 视觉与业务逻辑 (Day 5-6) 📋 计划中
- [ ] 实现图片上传和 VLM 识别
- [ ] 开发 RAG 关联和答案生成
- [ ] 设计 Chainlit 交互流程
- [ ] 实现错题记录机制

### Phase 4: 错题本与交付 (Day 7-8) 📋 计划中
- [ ] 完善错题本功能
- [ ] 实现作业清单解析
- [ ] 生成 PDF 错题报告
- [ ] 整体测试和 Prompt 优化

## 📝 会话管理规范

### 多会话开发

为确保项目开发的可追溯性，每次会话请遵循以下规范：

1. **初始化检查**: `./init.sh` 确保环境正常
2. **进度记录**: `claude-progress.txt` 记录会话进展
3. **功能验证**: `feature_list.json` 跟踪功能完成状态
4. **代码提交**: 每个功能完成后立即提交代码

## 🧪 质量保证

### 功能测试流程

1. 查阅 `feature_list.json` 了解当前进度
2. 选择特定功能进行开发测试
3. 按优先级顺序进行验证 (1=高, 2=中, 3=低)
4. 记录测试结果: `passes: false` → `passes: true`

### 代码规范

- **Python**: 使用 Black + Ruff 进行代码格式化和质量检查
- **文档**: 所有公共函数必须包含详细的 docstring
- **测试**: 每个功能模块都要有对应的单元测试
- **提交**: 使用语义化提交信息 (`feat:`, `fix:`, `docs:`)

### 日志和监控

```bash
# 查看服务日志
tail -f backend.log
tail -f frontend.log

# 查看初始化日志
tail -f init.log

# 连接数据库查看（使用容器内部psql）
docker exec -it homework-pal-postgres psql -U homeworkpal -d homeworkpal

# 或者使用外部psql（如果已安装psql客户端）
psql -h localhost -U homeworkpal -d homeworkpal

# 检查向量索引状态
SELECT * FROM pg_indexes WHERE tablename = 'textbook_knowledge';
```

## 🔧 常见问题

### 环境问题

1. **PostgreSQL 连接失败**
   ```bash
   # 检查 PostgreSQL 服务状态
   brew services list | grep postgresql
   # 启动 PostgreSQL
   brew services start postgresql
   ```

2. **pgvector 扩展未安装**
   ```sql
   -- 连接数据库后执行
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

3. **依赖安装失败**
   ```bash
   # 清理缓存重新安装
   uv cache clean
   uv sync --refresh
   ```

4. **端口占用问题**
   ```bash
   # 查看端口占用
   lsof -i :8000
   lsof -i :8001
   # 强制结束进程
   kill -9 <PID>
   ```

## 📞 支持与反馈

- **问题反馈**: 通过 GitHub Issues 提交
- **功能建议**: 查看 `feature_list.json` 中的规划功能
- **开发进度**: 查阅 `claude-progress.txt` 了解最新进展

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

---

**🌰 作业搭子**: 让每个孩子都能拥有贴心的作业辅导伙伴