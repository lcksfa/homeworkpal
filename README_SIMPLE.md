# Homework Pal 简化版快速启动指南

这个简化版本专注于测试前后端基本功能，暂时不连接数据库。

## 🚀 快速开始

### 方法1：自动测试（推荐）
自动启动服务、测试功能、然后停止服务：
```bash
./test_complete.sh
```

### 方法2：手动启动和测试
1. 启动服务：
```bash
./start_simple.sh
```
2. 在另一个终端运行测试：
```bash
./test_simple.sh
```

## 📁 文件说明

### 核心文件
- `start_simple.sh` - 服务启动脚本
- `test_complete.sh` - 完整测试脚本（自动启停服务）
- `test_simple.sh` - 简单测试脚本（需要服务已运行）
- `main_simple.py` - FastAPI后端（简化版）
- `app_simple.py` - Chainlit前端（简化版）

### 服务信息
- **后端API**: http://localhost:8001
- **前端界面 (浏览器)**: http://localhost:8000
- **API文档**: http://localhost:8001/docs

> **📝 重要说明**：
> - 服务器启动时显示 `0.0.0.0` 表示监听所有网络接口
> - 但在浏览器中访问时，请使用 `localhost` 或 `127.0.0.1`
> - `localhost:8000` 是浏览器访问的正确地址

## 🧪 测试结果

✅ **后端API测试**
- 根端点 (`/`) - 返回欢迎消息
- 健康检查 (`/health`) - 服务状态检查
- 状态API (`/api/v1/status`) - 系统状态信息

✅ **前端界面测试**
- 页面可访问性检查
- 基本交互功能

## 🔧 手动测试指南

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

## 📝 下一步

简化版验证通过后，你可以：
1. 运行 `./init.sh` 设置完整的开发环境
2. 按照项目文档添加RAG功能
3. 集成数据库和AI模型

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