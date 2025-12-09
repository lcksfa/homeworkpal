# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**作业搭子 (Homework Pal)** is an AI-powered homework assistant for 3rd grade students using 人教版 (PEP) textbooks with advanced RAG capabilities. The system helps students with homework checking, mistake tracking, and textbook knowledge retrieval using Chinese language models and vision processing.

## Core Architecture

### Technology Stack
- **Backend**: PostgreSQL + pgvector + FastAPI + SQLAlchemy
- **Frontend**: Chainlit (interactive web interface)
- **AI Engine**: Qwen/DeepSeek (Chinese LLMs) + BGE-M3 embedding model
- **Package Management**: uv (modern Python package manager)
- **Database**: PostgreSQL 16 with pgvector extension (Docker-based)
- **Development**: pytest + black + ruff

### System Components
- **RAG Core**: Document processing, vector search, and knowledge retrieval from PEP textbooks
- **Vision Service**: Image analysis for homework checking using Qwen-VL
- **Mistake Notebook**: Automatic mistake recording and review system
- **Interactive UI**: Chainlit-based chat interface with file upload capabilities

## Essential Commands

### Environment Setup and Management
```bash
# Full environment initialization (first-time setup)
./init.sh

# Development environment only (skip frontend)
./init.sh --no-frontend

# Reset vector database (WARNING: deletes all data)
./init.sh --reset-vectordb

# Use custom environment file
./init.sh --env .env.production

# Load and vectorize documents from path
./init.sh --load-docs ./textbooks
```

### Development Workflow
```bash
# Install dependencies
uv sync

# Install development dependencies
uv sync --dev

# Start frontend (Chainlit)
chainlit run app.py --host 0.0.0.0 --port 8000

# Start backend (FastAPI)
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

# Run tests
pytest

# Run specific module tests
pytest tests/test_document_processing.py
pytest tests/test_vision_grading.py

# Code formatting and linting
black src/
ruff check src/
```

### Database Operations
```bash
# Connect to PostgreSQL database
psql -h localhost -U homeworkpal -d homeworkpal

# Check database health
curl http://localhost:8001/health

# Check vector index status
SELECT * FROM pg_indexes WHERE tablename = 'textbook_knowledge';
```

### Docker Management
```bash
# Check PostgreSQL container status
docker ps | grep homework-pal-postgres

# View PostgreSQL logs
docker logs homework-pal-postgres

# Stop PostgreSQL container
docker stop homework-pal-postgres

# Start PostgreSQL container
docker start homework-pal-postgres
```

## Project Structure

```
homeworkpal/
├── app.py                    # Chainlit frontend application
├── main.py                   # FastAPI backend service
├── init.sh                   # Environment initialization script
├── pyproject.toml           # Python dependencies and project config
├── feature_list.json        # End-to-end feature testing checklist
├── claude-progress.txt      # Multi-session development progress log
├── .env                     # Environment variables (API keys, database config)
├── src/homeworkpal/         # Core Python package structure
│   ├── __init__.py
│   ├── core/               # Core business logic
│   ├── database/           # Database operations and models
│   ├── llm/               # LLM integrations (Qwen, DeepSeek)
│   ├── vision/            # Image processing and VLM integration
│   └── utils/             # Utility functions
├── docs/                   # Documentation and design specs
│   ├── 作业搭子产品文档.md
│   └── 开发任务分拆.md
├── tests/                  # Test suite
├── data/                   # Data storage
│   └── textbooks/         # PEP textbook materials
└── uploads/               # File upload directory
```

## Development Phases and Tasks

The project follows a structured 5-phase development approach with 40 detailed features tracked in `feature_list.json`:

### Phase 1: Infrastructure (Tasks 1.1-1.2)
- **Task-1.1**: Project initialization and environment configuration
- **Task-1.2**: Database model design (SQLAlchemy)

### Phase 2: RAG Core (Tasks 2.1-2.2)
- **Task-2.1**: Knowledge base ingestion script
- **Task-2.2**: RAG service implementation

### Phase 3: Vision & Logic (Tasks 3.1-3.2)
- **Task-3.1**: Vision service integration (Qwen-VL)
- **Task-3.2**: Mistake notebook CRUD service

### Phase 4: Frontend Integration (Tasks 4.1-4.3)
- **Task-4.1**: Chainlit chat framework and session management
- **Task-4.2**: Image upload and processing pipeline
- **Task-4.3**: "Add to Mistake Notebook" interaction

### Phase 5: Mistake Notebook (Tasks 5.1-5.2)
- **Task-5.1**: Mistake list display and rendering
- **Task-5.2**: Export functionality (Markdown download)

## Configuration Requirements

### Environment Variables (.env)
```bash
# Database Configuration
DATABASE_URL=postgresql://homeworkpal:password@localhost:5432/homeworkpal
DB_HOST=localhost
DB_PORT=5432
DB_NAME=homeworkpal
DB_USER=homeworkpal
DB_PASSWORD=password

# LLM API Configuration (configure at least one)
DASHSCOPE_API_KEY=your_dashscope_api_key_here    # Aliyun Qwen
DEEPSEEK_API_KEY=your_deepseek_api_key_here      # DeepSeek
OPENAI_API_KEY=your_openai_api_key_here          # OpenAI (optional)

# Vector Database Configuration
VECTOR_DIMENSION=1536
EMBEDDING_MODEL=BAAI/bge-m3

# Chainlit Configuration
CHAINLIT_HOST=0.0.0.0
CHAINLIT_PORT=8000
```

## Key Development Principles

### Single-Feature Development
- Each development session should focus on implementing **one specific feature**
- Use the `feature_list.json` to track progress (update `passes: false` → `passes: true`)
- Verify functionality with end-to-end testing before marking complete

### Environment Management
- Always run `./init.sh` at the start of development sessions to ensure environment health
- Use the provided skill commands for standardized operations:
  - `/rag开发会话` - Start standard development session
  - `/rag功能验证` - Verify specific functionality
  - `/rag状态报告` - Generate project status report
  - `/rag回滚恢复` - System rollback and recovery

### Quality Assurance
- All features must pass browser automation testing
- Use Chinese language for educational content (3rd grade level)
- Maintain encouraging tone suitable for young students
- Ensure all textbook references include proper citations and page numbers

### Code Standards
- Use `black` for code formatting and `ruff` for linting
- All public functions must include detailed docstrings
- Maintain test coverage for all functionality modules
- Use semantic commit messages (`feat:`, `fix:`, `docs:`)

## Testing and Validation

### Health Checks
```bash
# Check backend API health
curl http://localhost:8001/health

# Check frontend availability
curl http://localhost:8000

# Run system smoke tests
./init.sh  # includes built-in health checks
```

### Feature Validation
- Consult `feature_list.json` for current development status
- Use browser automation to test complete user journeys
- Verify textbook knowledge retrieval accuracy
- Test image processing and homework checking workflow

### Performance Monitoring
- Document processing success rate should exceed 95%
- Search response time should be under 500ms
- End-to-end response time should be under 2 seconds
- Generate answer relevance should exceed 85%

## Special Considerations

### Educational Context
- Target users: 3rd grade students (8-9 years old)
- Content: 人教版 (PEP) textbooks for Chinese elementary education
- Language: Simplified Chinese with age-appropriate vocabulary
- Tone: Encouraging, supportive, and educationally focused

### Technical Constraints
- PostgreSQL with pgvector extension is required for vector storage
- BGE-M3 embedding model optimized for Chinese content
- Chinese LLMs (Qwen/DeepSeek) for better cultural and educational context
- Docker-based PostgreSQL deployment for consistency

### Development Workflow
- Each session should update `claude-progress.txt` with detailed notes
- Git commits should be atomic and descriptive
- Use the established skill commands for standardized operations
- Maintain the engineering guardrails configured in `.claude/` directory

## Troubleshooting

### Common Issues
1. **Port conflicts**: PostgreSQL 5432, frontend 8000, backend 8001
2. **Vector database**: Ensure pgvector extension is enabled
3. **API keys**: Verify DASHSCOPE_API_KEY and DEEPSEEK_API_KEY configuration
4. **Environment**: Run `./init.sh` to verify complete setup

### Recovery Procedures
```bash
# Quick environment reset
./init.sh --reset-vectordb

# Full environment recovery
/rag回滚恢复 safe

# Check project status
/rag状态报告
```

## File References

- **README.md**: Comprehensive project documentation
- **feature_list.json**: 40 detailed features with test steps
- **claude-progress.txt**: Session-by-session development history
- **docs/开发任务分拆.md**: Detailed 5-phase development plan
- **.claude/**: Claude Code skill and agent configurations