启动作业搭子项目的标准开发会话。用于每次编码工作开始时，确保环境健康并选择下一个Homework Pal开发目标。

标准会话流程：
1. 环境状态检查
   - 确认当前工作目录（homeworkpal）
   - 读取最近20条git提交记录
   - 检查claude-progress.txt作业搭子进展状态

2. 开发环境启动
   - 执行./init.sh启动脚本（PostgreSQL + Chainlit + BGE-M3）
   - 验证Python虚拟环境状态（Python 3.11+）
   - 启动向量数据库（PostgreSQL + pgvector）
   - 启动后端API服务（FastAPI on port 8001）
   - 启动前端界面（Chainlit on port 8000）

3. 作业搭子系统健康检查
   - 后端API健康检查（http://localhost:8001/health）
   - PostgreSQL向量数据库连接验证
   - BGE-M3向量模型加载状态检查
   - 国产LLM API连接测试（Qwen/DeepSeek）
   - 基础人教版教材文档加载状态检查
   - 基础检索和作业批改功能冒烟测试

4. 功能目标选择
   - 读取feature_list.json作业搭子35项功能清单
   - 选择最高优先级的未通过功能（passes=false）
   - 确定本次会话的单一Homework Pal开发目标

5. 开发准备就绪
   - 确认作业搭子开发环境可正常运行
   - 明确本次会话要实现的具体教育场景功能
   - 准备开始小步增量开发（每次只实现一个功能）

使用时机：
- 每次开始新的作业搭子功能开发时
- 恢复中断的Homework Pal开发工作时
- 切换开发环境后重新开始时

输出要求：
- 环境状态检查的详细结果（包含教育技术栈状态）
- 选定的Homework Pal开发功能及其教育场景验收标准
- 当前作业搭子系统的健康状态和已知教育相关问题