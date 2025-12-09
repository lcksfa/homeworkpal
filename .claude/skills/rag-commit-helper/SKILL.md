---
name: rag-commit-helper
description: 基于暂存的差异生成可读的提交信息。在提交RAG项目变更前使用，自动分析代码变更并生成符合RAG项目规范的中文提交信息。
allowed-tools: Git, Read
---

# RAG项目提交信息助手

## 指令说明
- 运行git diff --staged并总结：<50字符摘要 + 详细说明>
- 包含影响的RAG模块和变更原因，不仅仅是变更内容

## RAG模块识别与变更分析

### 文档处理模块识别
```bash
# 检测文档处理相关文件变更
git diff --staged --name-only | grep -E "(document|parser|loader|chunk)"
```

#### 关键文件模式


### 检索模块识别
```bash
# 检测检索相关文件变更
git diff --staged --name-only | grep -E "(retrieval|search|vector|similarity)"
```

#### 关键文件模式


### 生成模块识别
```bash
# 检测生成相关文件变更
git diff --staged --name-only | grep -E "(generation|llm|prompt|chat)"
```

#### 关键文件模式


### 前端模块识别
```bash
# 检测前端相关文件变更
git diff --staged --name-only | grep -E "(ui|frontend|streamlit|static)"
```

## 提交信息生成逻辑

### 1. 分析变更类型
```python
def analyze_change_type(diff_output):
    if "def new_function" in diff_output or "class NewClass" in diff_output:
        return "feat"
    elif "fix" in diff_output or "except" in diff_output:
        return "fix"
    elif "refactor" in diff_output or "rename" in diff_output:
        return "refactor"
    elif "performance" in diff_output or "optimize" in diff_output:
        return "perf"
```

### 2. 识别影响范围
```python
def identify_rag_scope(changed_files):
    scope = []
    if any("document" in f for f in changed_files):
        scope.append("document")
    if any("retrieval" in f for f in changed_files):
        scope.append("retrieval")
    if any("generation" in f for f in changed_files):
        scope.append("generation")
    if any("ui" in f or "frontend" in f for f in changed_files):
        scope.append("ui")
    return "+".join(scope) if scope else "core"
```

### 3. 生成提交信息
```python
def generate_commit_title(change_type, scope, description):
    return f"{change_type}({scope}): {description}"

def generate_commit_body(changed_files, rag_impact, testing_notes):
    body = "## 变更模块\n"
    body += f"- 影响文件: {', '.join(changed_files)}\n\n"
    body += "## RAG流程影响\n"
    body += f"- {rag_impact}\n\n"
    body += "## 测试验证\n"
    body += f"- {testing_notes}\n"
    return body
```

## 生成的提交信息示例

### 文档处理功能
```
feat(document): 新增PDF文档解析和向量化功能

## 变更模块
- 影响文件: src/document_processor.py, src/vector_store.py, tests/test_documents.py

## RAG流程影响
- 文档处理：新增PDF解析器，支持文本和图像提取
- 向量化：改进文档分段策略，提升语义相似度
- 索引：自动文档元数据提取和存储

## 测试验证
- 单元测试：PDF解析准确性 98%
- 集成测试：向量化处理速度 <2秒/文档
- E2E测试：上传PDF到可检索的完整流程
```

### 检索算法优化
```
perf(retrieval): 优化混合检索算法，提升查询准确率15%

## 变更模块
- 影响文件: src/retriever.py, src/similarity.py, src/ranking.py

## RAG流程影响
- 检索过程：结合BM25和语义相似度的混合检索
- 排序优化：引入相关性重排序机制
- 性能提升：查询响应时间减少30%

## 测试验证
- 准确率测试：标准测试集准确率从82%提升至97%
- 性能测试：平均查询时间从1.2秒降至0.8秒
- 回归测试：现有功能无异常
```

### 错误修复
```
fix(generation): 修复长上下文处理中的截断错误

## 变更模块
- 影响文件: src/generator.py, src/context_manager.py

## RAG流程影响
- 生成质量：修复超过token限制时的上下文截断
- 错误处理：增加优雅的fallback机制
- 用户体验：添加上下文长度提示

## 测试验证
- 边界测试：长文档处理不再出现截断错误
- 回归测试：短文本生成功能正常
- 用户测试：界面提示清晰，体验改善
```

## 使用指令
1. 在暂存变更后运行此技能
2. 自动分析变更内容和影响范围
3. 生成符合RAG项目规范的提交信息
4. 提供编辑机会让用户完善描述
5. 输出最终的可提交信息格式