---
name: rag-rollback
description: 快速回滚RAG项目的错误变更并恢复工作状态。在冒烟测试/E2E失败或出现回归时使用，确保RAG系统各组件（文档处理、检索、生成）的稳定性。
allowed-tools: Git, Bash, Read
---

# RAG项目回滚恢复

## 指令说明
- 使用git revert或快照恢复；优先选择最小影响范围
- 重新运行init.sh和E2E冒烟测试确认恢复状态
- 在进度笔记中记录事件根本原因

## RAG系统回滚场景

### 文档处理问题
#### 症状
- 新上传文档无法解析
- 向量化过程失败
- 文档元数据丢失
- 分段策略异常

#### 回滚策略
```bash
# 回滚到最近的文档处理稳定版本
git log --oneline --grep="document" -5
git revert <commit-hash>

# 验证文档处理恢复
python scripts/test_document_processing.py
curl http://localhost:8000/documents/count
```

### 检索功能问题
#### 症状
- 查询返回空结果
- 检索结果相关性差
- 相似度计算异常
- 向量索引损坏

#### 回滚策略
```bash
# 回滚检索相关变更
git log --oneline --grep="retrieval" -5
git revert <commit-hash>

# 重建向量索引（如果需要）
python scripts/rebuild_vector_index.py

# 验证检索功能
curl -X POST http://localhost:8000/retrieve \
  -H "Content-Type: application/json" \
  -d '{"query": "测试查询", "top_k": 3}'
```

### 生成功能问题
#### 症状
- LLM生成回答异常
- API调用失败
- 生成质量下降
- 上下文处理错误

#### 回滚策略
```bash
# 回滚生成功能相关变更
git log --oneline --grep="generation" -5
git revert <commit-hash>

# 测试生成功能
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "测试查询", "context_length": 2000}'
```

### 前端界面问题
#### 症状
- 界面无法加载
- 用户交互失效
- 样式显示异常
- JavaScript错误

#### 回滚策略
```bash
# 回滚前端相关变更
git log --oneline --grep="ui\|frontend" -5
git revert <commit-hash>

# 重启前端服务
pkill -f "streamlit\|npm.*start"
./init.sh --frontend-only
```

## 紧急恢复流程

### 1. 快速评估
```bash
# 检查当前状态
git status
git log --oneline -5
./init.sh --health-check
```

### 2. 识别问题范围
```bash
# 运行分类测试
python scripts/test_document_processing.py
python scripts/test_retrieval.py
python scripts/test_generation.py
python scripts/test_frontend.py
```

### 3. 选择回滚策略
```bash
# 选项A：回滚最近一个提交（安全）
git revert HEAD

# 选项B：回滚到已知良好状态
git log --oneline -10 | grep "feat.*RAG-[0-9]*"
git reset --hard <good-commit-hash>

# 选项C：选择性回滚模块
git revert <commit-hash-1> <commit-hash-2>
```

### 4. 验证恢复
```bash
# 重新初始化环境
./init.sh --full-reset

# 运行完整E2E测试
python scripts/e2e_smoke.py
```

## 事故记录模板

在claude-progress.txt中记录：
```
[rollback] ISO8601时间戳
incident_type: <document|retrieval|generation|ui|system>
root_cause: <问题根本原因分析>
affected_commits: <回滚的提交哈希列表>
recovery_action: <采取的恢复措施>
verification: <恢复验证结果>
prevention: <防止再次发生的措施>
impact_assessment: <对用户和系统的影响评估>
```

## 预防措施

### 提交前检查
- 运行相关模块的单元测试
- 执行冒烟测试验证
- 检查配置文件变更影响
- 验证外部依赖兼容性

### 渐进式部署
- 先在测试环境验证
- 分阶段部署到生产
- 监控关键指标变化
- 准备快速回滚方案

### 数据备份
- 定期备份向量数据库
- 保存模型检查点
- 记录配置文件变更历史
- 维护测试数据集