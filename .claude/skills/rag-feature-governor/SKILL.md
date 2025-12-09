---
name: rag-feature-governor
description: 管理RAG项目的端到端功能清单feature_list.json。用于将用户需求扩展为完整的RAG功能测试项，强制执行数据结构规范，仅在E2E验证后更新通过状态。
allowed-tools: Read, Write, Grep
---

# RAG功能清单治理器

## 数据结构规范
```json
{
  "id": "HomeworkPal-XXX",
  "category": "functional|performance|reliability|ui",
  "description": "功能描述，覆盖用户场景的端到端流程",
  "steps": [
    "步骤1：用户操作或系统状态",
    "步骤2：HomeworkPal系统处理流程",
    "步骤3：预期结果或验证点"
  ],
  "priority": 1,
  "passes": false
}
```

## HomeworkPal功能类别示例

### 文档处理功能
- 文档上传与解析（PDF、TXT、MD）
- 文档分段与向量化
- 文档元数据提取与索引

### 检索功能
- 语义相似度搜索
- 混合检索（语义+关键词）
- 检索结果排序与过滤

### 生成功能
- 基于检索内容的回答生成
- 上下文长度管理
- 回答质量验证

### 用户界面功能
- 文档管理界面
- 查询输入与历史记录
- 结果展示与引用来源

## 指令说明
- 将用户提示扩展为全面的RAG端到端功能，初始设置passes=false
- 后续仅：在E2E证明后更新单个功能的passes=true
- 拒绝编辑description/steps；如果步骤有误，添加新功能项并通过治理笔记废弃旧项（不删除）

## 治理规则
- 初始化后，只有passes字段可修改
- 每个功能必须包含完整的用户到系统的流程验证
- 优先级排序：核心检索功能 > 文档处理 > 用户界面 > 性能优化
- 禁止删除功能项，只能标记废弃并添加新项