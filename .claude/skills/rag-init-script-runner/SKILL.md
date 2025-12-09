---
name: rag-init-script-runner
description: 为RAG项目创建并运行可重现的初始化脚本。包含Python虚拟环境、依赖安装、向量数据库初始化、文档加载、服务启动和健康检查。在项目启动和每次编码会话前使用。
allowed-tools: Read, Write, Bash, Git
---

# RAG项目初始化脚本执行器

## 指令说明
- 检测RAG项目结构（前端/后端分离、向量数据库、文档存储）
- 生成支持多种配置的init.sh脚本：--no-frontend, --reset-vectordb, --env FILE, --load-docs PATH
- 包含：Python虚拟环境创建、uv依赖安装、向量数据库初始化、可选文档加载、启动FastAPI/chainlit服务、健康检查、E2E冒烟测试
- 确保脚本幂等性，提供详细日志和错误处理
- 失败时停止并将原因写入claude-progress.txt

## RAG项目特定模块
- Python虚拟环境与依赖管理（uv, pyproject.toml）
- 向量数据库设置（配置与初始化）
- 文档处理管道（PDF/TXT/MD文档加载与向量化）
- 后端服务启动（FastAPI + Uvicorn）
- 前端服务启动（chainlit）
- 健康检查端点验证
- 基础RAG功能冒烟测试

## 示例脚本结构
```bash
#!/bin/bash
# 参数解析与环境变量加载
# Python虚拟环境创建与激活
# 依赖安装（uv sync）
# 向量数据库初始化与配置
# 可选：示例文档加载与向量化
# 后端服务启动（uvicorn）
# 可选：前端服务启动（chainlit run）
# 健康检查与基础功能测试
```

## 使用场景
- 项目首次搭建时生成完整的初始化脚本
- 每次编码会话开始前一键启动开发环境
- 环境损坏时的快速恢复机制