# Textbook Processing Usage Guide

## 📚 教材处理模块使用指南

### 快速开始

#### 1. 使用统一命令行工具

```bash
# 进入项目目录
cd /Users/lizhao/workspace/hulus/homeworkpal

# 激活虚拟环境
source .venv/bin/activate

# 运行基础教材导入
python textbook_processing/run_textbook_processing.py basic

# 运行增强教材导入
python textbook_processing/run_textbook_processing.py enhanced

# 运行结构化教材导入
python textbook_processing/run_textbook_processing.py structured

# 运行完整的中文教材处理流程
python textbook_processing/run_textbook_processing.py chinese

# 运行测试
python textbook_processing/run_textbook_processing.py test
```

#### 2. 直接运行单个脚本

```bash
# 中文教材处理流程
python textbook_processing/pdf_processing/process_chinese_textbook.py
python textbook_processing/export/export_textbook_to_csv.py
python textbook_processing/ingestion/import_chinese_textbook.py

# 测试功能
python textbook_processing/tests/test_chinese_vectorize.py
python textbook_processing/tests/test_chinese_search.py
```

### 📁 文件说明

#### ingestion/ - 导入脚本
- `ingest_textbooks.py` - 基础PDF教材导入
- `ingest_textbooks_enhanced.py` - 增强版导入，包含质量评估
- `ingest_textbooks_structured.py` - 结构化导入
- `import_chinese_textbook.py` - 语文教材专用导入（已验证可用）

#### pdf_processing/ - PDF处理
- `process_chinese_textbook.py` - 中文教材PDF处理

#### export/ - 数据导出
- `export_textbook_to_csv.py` - 教材内容导出为CSV

#### tests/ - 测试脚本
- `test_chinese_search.py` - 中文检索测试
- `test_chinese_vectorize.py` - 向量化测试

#### scripts/ - 工具脚本
- `chinese_textbook_vectorize.py` - 语文教材向量化脚本

### 🎯 推荐使用流程

#### 完整的语文教材处理流程
```bash
# 1. 运行完整的中文处理流程
python textbook_processing/run_textbook_processing.py chinese

# 2. 验证结果
python textbook_processing/run_textbook_processing.py test
```

#### 其他教材导入
```bash
# 基础导入（推荐用于新教材）
python textbook_processing/run_textbook_processing.py basic

# 增强导入（包含质量评估）
python textbook_processing/run_textbook_processing.py enhanced
```

### ⚙️ 环境要求

确保以下环境变量已设置：
```bash
SILICONFLOW_API_KEY=your_api_key_here
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
DATABASE_URL=postgresql://homeworkpal:password@localhost:5432/homeworkpal
```

### 📂 数据文件位置

- PDF教材文件: `data/textbooks/`
- 导出的CSV文件: `exports/`
- 数据库: PostgreSQL (通过Docker运行)

### 🔍 验证导入结果

```bash
# 检查数据库中的教材内容
docker exec homework-pal-postgres psql -U homeworkpal -d homeworkpal -c "SELECT COUNT(*) FROM textbook_chunks;"

# 检查中文教材内容
docker exec homework-pal-postgres psql -U homeworkpal -d homeworkpal -c "SELECT COUNT(*) FROM textbook_chunks WHERE source_file LIKE '%语文%';"
```

### 🚨 常见问题

1. **API密钥错误**: 确保SILICONFLOW_API_KEY有效
2. **数据库连接失败**: 确保PostgreSQL容器正在运行
3. **PDF文件不存在**: 确保PDF文件在`data/textbooks/`目录下
4. **内存不足**: 处理大文件时建议分批处理

### 📊 成功指标

- ✅ 成功导入128个语文教材片段
- ✅ 生成1024维向量嵌入
- ✅ 完整的元数据结构
- ✅ 支持智能检索