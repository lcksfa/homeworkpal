---
name: rag-e2e-smoke
description: 运行RAG项目的最小端到端冒烟测试。在实现任何新功能前的会话开始时使用，确保核心RAG流程（文档加载→检索→生成）正常运行。
allowed-tools: Read, Bash, Browser
---

# RAG端到端冒烟测试

## 测试范围
- 后端健康检查（/health 端点返回200）
- 向量数据库连接状态
- 示例文档已加载并向量化
- 基础检索功能测试（查询能返回相关文档片段）
- 生成功能测试（基于检索结果生成回答）
- 如有前端：界面可访问，能提交查询并收到结果

## RAG核心流程验证

### 1. 系统健康检查
```bash
curl http://localhost:8000/health
# 期望：{"status": "healthy", "vector_db": "connected", "models": "loaded"}
```

### 2. 文档处理验证
```bash
curl http://localhost:8000/documents/count
# 期望：文档数量 > 0

curl http://localhost:8000/documents/sample
# 期望：返回示例文档的向量化和元数据信息
```

### 3. 检索功能测试
```bash
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是机器学习？", "top_k": 3}'
# 期望：返回相关文档片段列表
```

### 4. 生成功能测试
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "什么是机器学习？", "context_length": 2000}'
# 期望：基于检索结果生成的回答
```

### 5. 前端界面测试（如果存在）
- 浏览器访问 http://localhost:8501（chainlit）或其他前端端口
- 界面正常加载，无JavaScript错误
- 能输入查询并提交
- 显示加载状态和最终结果

## 指令说明
- 快速失败；如果任何检查失败，停止功能工作并优先修复环境
- 生成简短的通过/失败信号和证据行
- 记录每个步骤的响应时间和结果
- 如果测试失败，详细记录失败原因到claude-progress.txt

## 失败处理
- 向量数据库连接失败 → 检查配置和启动脚本
- 文档未加载 → 运行文档加载流程
- 检索无结果 → 检查文档内容和向量化过程
- 生成失败 → 检查LLM模型配置和API密钥
- 前端错误 → 检查前端服务启动状态