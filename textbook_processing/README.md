# Textbook Processing Module

教材处理模块 - 负责PDF教材的解析、分块、向量化导入和检索测试

## 目录结构

### 📁 ingestion/ - 教材导入脚本
- **`ingest_textbooks.py`** - 基础教材导入脚本
  - 功能：从PDF文件中提取文本并进行基础分块
  - 输入：PDF文件路径
  - 输出：数据库中的文本片段

- **`ingest_textbooks_enhanced.py`** - 增强版教材导入脚本
  - 功能：在基础版本上增加了更智能的分块和质量评估
  - 特点：支持多种分块策略和质量评分

- **`ingest_textbooks_structured.py`** - 结构化教材导入脚本
  - 功能：基于CSV预处理的结构化导入
  - 特点：支持预定义的单元和课文结构

- **`import_chinese_textbook.py`** - 语文教材专用导入脚本
  - 功能：从CSV文件导入已处理好的语文教材内容
  - 特点：使用SiliconFlow BGE-M3模型生成向量嵌入
  - 元数据：包含完整的单元、课文、页码信息

### 📁 pdf_processing/ - PDF处理脚本
- **`process_chinese_textbook.py`** - 中文教材PDF处理脚本
  - 功能：专门处理中文语文教材PDF文件
  - 特点：支持中文文本的智能解析和结构化提取

### 📁 export/ - 数据导出脚本
- **`export_textbook_to_csv.py`** - 教材内容导出脚本
  - 功能：将数据库中的教材内容导出为CSV格式
  - 用途：数据预处理、备份、分析

### 📁 tests/ - 测试脚本
- **`test_chinese_search.py`** - 中文检索测试脚本
  - 功能：测试中文教材内容的检索功能
  - 特点：支持关键词搜索和语义搜索

- **`test_chinese_vectorize.py`** - 向量化测试脚本
  - 功能：测试向量嵌入生成和相似度计算
  - 特点：验证BGE-M3模型的中文支持

### 📁 scripts/ - 工具脚本
- **`chinese_textbook_vectorize.py`** - 语文教材向量化脚本
  - 功能：集成化的语文教材向量化流程
  - 特点：包含数据处理、向量化、导入的完整流程

## 使用方法

### 1. 基础导入流程
```bash
# 基础导入
python textbook_processing/ingestion/ingest_textbooks.py

# 增强导入
python textbook_processing/ingestion/ingest_textbooks_enhanced.py

# 结构化导入
python textbook_processing/ingestion/ingest_textbooks_structured.py
```

### 2. 语文教材专用流程
```bash
# 处理PDF并导出CSV
python textbook_processing/pdf_processing/process_chinese_textbook.py
python textbook_processing/export/export_textbook_to_csv.py

# 向量化导入
python textbook_processing/ingestion/import_chinese_textbook.py
```

### 3. 测试和验证
```bash
# 检索测试
python textbook_processing/tests/test_chinese_search.py

# 向量化测试
python textbook_processing/tests/test_chinese_vectorize.py
```

## 技术栈

- **PDF处理**: PyMuPDF, unstructured
- **文本分块**: 自定义智能分块算法
- **向量嵌入**: SiliconFlow BGE-M3模型
- **数据库**: PostgreSQL + pgvector
- **测试框架**: pytest

## 数据流程

1. **PDF解析** → 提取原始文本内容
2. **智能分块** → 按课文、段落进行结构化分块
3. **质量评估** → 评估文本质量和可读性
4. **向量化** → 生成1024维嵌入向量
5. **数据库存储** → 存储到PostgreSQL + pgvector
6. **检索测试** → 验证检索质量和准确性

## 配置要求

确保环境变量已正确配置：
```bash
SILICONFLOW_API_KEY=your_api_key_here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
DATABASE_URL=postgresql://user:pass@localhost:5432/homeworkpal
```

## 注意事项

1. **文件路径**: PDF文件应放在 `data/textbooks/` 目录下
2. **数据库**: 确保PostgreSQL数据库已启动并配置pgvector扩展
3. **API密钥**: SiliconFlow API密钥需要有效额度支持向量化
4. **内存使用**: 大文件处理时注意内存使用情况