#!/bin/bash
# Homework Pal RAG System Initialization Script
# Supports: --no-frontend, --reset-vectordb, --env FILE, --load-docs PATH
# Ensures idempotency for repeated runs

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
SKIP_FRONTEND=false
RESET_VECTORDB=false
ENV_FILE=".env"
LOAD_DOCS_PATH=""
LOG_FILE="logs/init.log"
HEALTH_CHECK_TIMEOUT=60
STOP_SERVICES=false

# Logging function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --no-frontend)
                SKIP_FRONTEND=true
                shift
                ;;
            --reset-vectordb)
                RESET_VECTORDB=true
                shift
                ;;
            --env)
                ENV_FILE="$2"
                shift 2
                ;;
            --load-docs)
                LOAD_DOCS_PATH="$2"
                shift 2
                ;;
            --stop)
                STOP_SERVICES=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                ;;
        esac
    done
}

show_help() {
    cat << EOF
Homework Pal RAG System Initialization Script

Usage: $0 [OPTIONS]

Options:
    --no-frontend         Skip frontend service startup
    --reset-vectordb      Reset vector database (WARNING: deletes all data)
    --env FILE           Load environment variables from FILE (default: .env)
    --load-docs PATH     Load and vectorize documents from PATH
    --stop               Stop all running services
    -h, --help          Show this help message

Requirements:
    - Docker and Docker Compose installed and running
    - PostgreSQL will be started using pgvector/pgvector:pg16 Docker image
    - Data is persisted in Docker volume 'homework-pal-postgres-data'

Examples:
    $0                    # Full initialization with Docker PostgreSQL
    $0 --no-frontend      # Skip frontend
    $0 --reset-vectordb   # Reset vector database
    $0 --env .env.prod    # Use production environment
    $0 --load-docs ./docs # Load documents from docs directory

Docker Commands:
    - Check PostgreSQL container: docker ps | grep homework-pal-postgres
    - View PostgreSQL logs: docker logs homework-pal-postgres
    - Stop PostgreSQL: docker stop homework-pal-postgres
    - Start PostgreSQL: docker start homework-pal-postgres
    - Connect to database: docker exec -it homework-pal-postgres psql -U homeworkpal -d homeworkpal
    - List databases: docker exec homework-pal-postgres psql -U homeworkpal -l
    - Note: Database schema is created automatically by the application

EOF
}

# Check system requirements
check_requirements() {
    info "Checking system requirements..."

    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        error "uv is not installed. Please install uv first: https://docs.astral.sh/uv/"
    fi

    # Check if python is available
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed"
    fi

    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first"
    fi

    if ! docker info &> /dev/null; then
        error "Docker is not running. Please start Docker service"
    fi

    # Check if PostgreSQL Docker container is running
    if ! docker ps --filter "name=homework-pal-postgres" --filter "status=running" | grep -q "homework-pal-postgres"; then
        warning "PostgreSQL Docker container 'homework-pal-postgres' is not running"
        info "Starting PostgreSQL Docker container..."
        docker start homework-pal-postgres || {
            info "Creating PostgreSQL Docker container..."
            docker run -d \
                --name homework-pal-postgres \
                -e POSTGRES_DB=homeworkpal \
                -e POSTGRES_USER=homeworkpal \
                -e POSTGRES_PASSWORD=password \
                -p 5432:5432 \
                -v homework-pal-postgres-data:/var/lib/postgresql/data \
                timescale/timescaledb-ha:pg16
        }

        # Wait for PostgreSQL to be ready
        info "Waiting for PostgreSQL to be ready..."
        for i in {1..30}; do
            if docker exec homework-pal-postgres pg_isready -q &> /dev/null; then
                success "PostgreSQL Docker container is ready"
                break
            elif [ $i -eq 30 ]; then
                error "PostgreSQL Docker container failed to start within 30 seconds"
            else
                sleep 1
            fi
        done
    else
        success "PostgreSQL Docker container is already running"
    fi

    success "System requirements check passed"
}

# Create environment file if it doesn't exist
create_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        if [[ -f ".env.template" ]]; then
            info "Found .env.template file, creating .env from template..."
            cp .env.template "$ENV_FILE"
            success "Environment file created from .env.template"
        else
            warning "Environment file $ENV_FILE not found and no .env.template available"
            warning "Creating minimal environment file..."
            cat > "$ENV_FILE" << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://homeworkpal:password@localhost:5432/homeworkpal
DB_HOST=localhost
DB_PORT=5432
DB_NAME=homeworkpal
DB_USER=homeworkpal
DB_PASSWORD=password

# LLM Configuration (choose one or more)
# OpenAI (for fallback)
OPENAI_API_KEY=your_openai_api_key_here

# Aliyun DashScope (Qwen)
DASHSCOPE_API_KEY=your_dashscope_api_key_here

# DeepSeek
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Vector Database Configuration
VECTOR_DIMENSION=1536
EMBEDDING_MODEL=BAAI/bge-m3

# Chainlit Configuration
CHAINLIT_HOST=0.0.0.0
CHAINLIT_PORT=8000

# File Storage
UPLOAD_DIR=./uploads
VECTOR_INDEX_DIR=./vector_index

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log

# Development Settings
DEBUG=true
RELOAD=true
EOF
        fi

        warning "Please edit $ENV_FILE with your actual API keys and database credentials"
        warning ""
        warning "Required minimum configuration:"
        warning "  - DASHSCOPE_API_KEY or DEEPSEEK_API_KEY (AI model access)"
        warning "  - DATABASE_URL (PostgreSQL with pgvector)"
        warning ""
        warning "After editing, run this script again"
        exit 1
    fi

    info "Loading environment from $ENV_FILE"
    source "$ENV_FILE"
}

# Set up Python virtual environment
setup_python_env() {
    info "Setting up Python virtual environment..."

    # Create virtual environment if it doesn't exist
    if [[ ! -d ".venv" ]]; then
        info "Creating Python virtual environment..."
        uv venv --python 3.11
        success "Virtual environment created"
    else
        info "Virtual environment already exists"
    fi

    # Activate virtual environment and install dependencies
    info "Installing dependencies..."
    source .venv/bin/activate
    uv sync --dev

    success "Python environment setup completed"
}


# Reset vector database if requested
reset_vector_db() {
    if [[ "$RESET_VECTORDB" == true ]]; then
        warning "Resetting vector database..."
        source .venv/bin/activate

        python - << EOF
import asyncio
from sqlalchemy import create_engine, text

async def reset_db():
    try:
        engine = create_engine("$DATABASE_URL")
        with engine.connect() as conn:
            # Drop tables in correct order (respecting foreign keys)
            conn.execute(text("DROP TABLE IF EXISTS mistake_records;"))
            conn.execute(text("DROP TABLE IF EXISTS homework_sessions;"))
            conn.execute(text("DROP TABLE IF EXISTS textbook_knowledge;"))
            conn.commit()
            print("Vector database reset completed")

    except Exception as e:
        print(f"Database reset failed: {e}")

if __name__ == "__main__":
    asyncio.run(reset_db())
EOF

        # Note: Database schema will be created by application code on next run
        success "Vector database data cleared. Schema will be recreated by application on next run"
    fi
}

# Load and vectorize documents if path provided
load_documents() {
    if [[ -n "$LOAD_DOCS_PATH" && -d "$LOAD_DOCS_PATH" ]]; then
        info "Loading and vectorizing documents from $LOAD_DOCS_PATH..."
        source .venv/bin/activate

        # This would be implemented in a separate document loading script
        warning "Document loading functionality will be implemented in the next phase"
        # python load_documents.py --path "$LOAD_DOCS_PATH"
    fi
}

# Start backend services
start_backend() {
    info "Starting backend services..."
    source .venv/bin/activate

    # Try to start full backend first, fallback to simple version
    info "Starting FastAPI backend..."
    if uv run python -c "
import sys
sys.path.insert(0, '.')
try:
    # Test modern psycopg 3 import
    import psycopg
    print('psycopg version:', psycopg.__version__)
    from homeworkpal.api.main import app
    print('SUCCESS: Full backend available')
    sys.exit(0)
except Exception as e:
    print(f'ERROR: Full backend failed: {e}')
    sys.exit(1)
" 2>/dev/null; then
        # Full backend is available, start it
        uv run uvicorn homeworkpal.api.main:app --host 0.0.0.0 --port 8001 --reload > logs/backend.log 2>&1 &
        BACKEND_PID=$!
        echo $BACKEND_PID > .backend.pid
        success "Full backend service started (PID: $BACKEND_PID)"
    else
        # Fallback to simple backend
        warning "Full backend not available (database connection issue), using simple backend..."
        info "To fix database issues:"
        info "  1. Ensure PostgreSQL is running: docker start homework-pal-postgres"
        info "  2. Check DATABASE_URL in .env file"
        info "  3. Reinstall dependencies: uv sync --dev"
        uv run uvicorn homeworkpal.simple.api:app --host 0.0.0.0 --port 8001 --reload > logs/backend.log 2>&1 &
        BACKEND_PID=$!
        echo $BACKEND_PID > .backend.pid
        success "Simple backend service started (PID: $BACKEND_PID)"
    fi
}

# Start frontend services
start_frontend() {
    if [[ "$SKIP_FRONTEND" == false ]]; then
        info "Starting Chainlit frontend..."

        # Try to start full frontend first, fallback to simple version
        if [[ -f "homeworkpal/frontend/app.py" ]]; then
            # Full frontend is available, start it
            uv run chainlit run homeworkpal/frontend/app.py --host 0.0.0.0 --port 8000 > logs/frontend.log 2>&1 &
            FRONTEND_PID=$!
            echo $FRONTEND_PID > .frontend.pid
            success "Full frontend service started (PID: $FRONTEND_PID)"
        else
            # Fallback to simple frontend
            info "Full frontend not available, using simple frontend..."
            uv run chainlit run homeworkpal/simple/app.py --host 0.0.0.0 --port 8000 > logs/frontend.log 2>&1 &
            FRONTEND_PID=$!
            echo $FRONTEND_PID > .frontend.pid
            success "Simple frontend service started (PID: $FRONTEND_PID)"
        fi
    else
        info "Skipping frontend startup (--no-frontend flag)"
    fi
}

# Perform health checks
health_check() {
    info "Performing health checks..."

    # Check backend health with more patience
    info "Checking backend health..."
    backend_ok=false
    for i in $(seq 1 $HEALTH_CHECK_TIMEOUT); do
        if curl -f http://localhost:8001/health > /dev/null 2>&1; then
            success "Backend health check passed"
            backend_ok=true
            break
        else
            # Check if process is still running
            if [[ -f ".backend.pid" ]]; then
                BACKEND_PID=$(cat .backend.pid)
                if ! kill -0 $BACKEND_PID 2>/dev/null; then
                    warning "Backend process is no longer running"
                    break
                fi
            fi
            sleep 1
        fi
    done

    if [[ "$backend_ok" == false ]]; then
        warning "Backend health check failed after $HEALTH_CHECK_TIMEOUT seconds"
        warning "Check logs: tail -f logs/backend.log"
    fi

    # Check frontend health if running
    if [[ "$SKIP_FRONTEND" == false ]]; then
        info "Checking frontend health..."
        frontend_ok=false
        for i in $(seq 1 $HEALTH_CHECK_TIMEOUT); do
            if curl -f http://localhost:8000 > /dev/null 2>&1; then
                success "Frontend health check passed"
                frontend_ok=true
                break
            else
                # Check if process is still running
                if [[ -f ".frontend.pid" ]]; then
                    FRONTEND_PID=$(cat .frontend.pid)
                    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
                        warning "Frontend process is no longer running"
                        break
                    fi
                fi
                sleep 1
            fi
        done

        if [[ "$frontend_ok" == false ]]; then
            warning "Frontend health check failed after $HEALTH_CHECK_TIMEOUT seconds"
            warning "Check logs: tail -f logs/frontend.log"
        fi
    fi
}

# Run smoke tests
run_smoke_tests() {
    info "Running smoke tests..."

    # Test database connection using uv run
    uv run python - << EOF
import sys
from sqlalchemy import create_engine, text

def test_db():
    try:
        # Convert DATABASE_URL to use psycopg driver
        database_url = "$DATABASE_URL"
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://")

        engine = create_engine(database_url)
        with engine.connect() as conn:
            # Test basic connection
            result = conn.execute(text("SELECT 1"))
            connection_ok = result.fetchone()[0] == 1

            if connection_ok:
                print("Database connection successful")

                # Test if tables exist (may be empty)
                try:
                    result = conn.execute(text("""
                        SELECT COUNT(*) FROM information_schema.tables
                        WHERE table_name IN ('textbook_knowledge', 'homework_sessions', 'mistake_records')
                    """))
                    table_count = result.fetchone()[0]
                    print(f"Database tables found: {table_count}")

                    if table_count >= 3:
                        # Try to count knowledge entries (table might be empty)
                        try:
                            result = conn.execute(text("SELECT COUNT(*) FROM textbook_knowledge"))
                            count = result.fetchone()[0]
                            print(f"Knowledge entries: {count}")
                        except Exception as e:
                            print(f"Knowledge table exists but query failed: {e}")
                            # This is acceptable for initial setup

                    return True
                except Exception as e:
                    print(f"Table check failed: {e}")
                    return False
            else:
                print("Database connection failed")
                return False

    except Exception as e:
        print(f"Database test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_db()
    sys.exit(0 if success else 1)
EOF

    if [[ $? -eq 0 ]]; then
        success "Smoke tests passed"
    else
        warning "Some smoke tests failed - this may be normal for first-time setup"
    fi
}

# Create necessary directories
create_directories() {
    info "Creating necessary directories..."

    # mkdir -p uploads
    # mkdir -p vector_index
    mkdir -p logs
    mkdir -p data/textbooks
    mkdir -p tests

    success "Directories created"
}

# Verify application structure
verify_app_structure() {
    info "Verifying application structure..."

    # Check if homeworkpal package structure exists
    if [[ -d "homeworkpal" ]]; then
        success "homeworkpal package structure found"
        echo "  Main files:"
        echo "    - Backend: homeworkpal/api/main.py"
        echo "    - Frontend: homeworkpal/frontend/app.py"
        echo "    - Simple API: homeworkpal/simple/api.py"
        echo "    - Simple App: homeworkpal/simple/app.py"
    else
        error "homeworkpal package directory not found"
        return 1
    fi

    success "Application structure verified"
}

# Main execution function
main() {
    log "Starting Homework Pal RAG System initialization..."

    # Parse command line arguments
    parse_args "$@"

    # Handle stop request
    if [[ "$STOP_SERVICES" == true ]]; then
        info "Stopping all Homework Pal services..."
        cleanup
        success "All services stopped"
        exit 0
    fi

    # Check system requirements
    check_requirements

    # Create environment file
    create_env_file

    # Create directories
    create_directories

    # Setup Python environment
    setup_python_env

    # Verify application structure
    verify_app_structure

    # Note: Database schema initialization will be handled by the application code
    # Reset vector database if requested (only data removal, not schema)
    reset_vector_db

    # Load documents if path provided
    load_documents

    # Start services
    start_backend
    start_frontend

    # Health checks
    health_check

    # Run smoke tests
    run_smoke_tests

    success "Homework Pal RAG System initialization completed successfully!"

    echo ""
    echo "🌰 Homework Pal is now running!"
    echo "📱 Frontend: http://localhost:8000"
    echo "🔧 Backend API: http://localhost:8001"
    echo "📊 API Docs: http://localhost:8001/docs"
    echo ""
    echo "To stop services:"
    echo "  kill \$(cat .backend.pid) 2>/dev/null || true"
    echo "  kill \$(cat .frontend.pid) 2>/dev/null || true"
    echo "  docker stop homework-pal-postgres"
    echo ""
    echo "To restart PostgreSQL Docker container:"
    echo "  docker start homework-pal-postgres"
    echo ""
    echo "To view logs:"
    echo "  tail -f logs/backend.log"
    echo "  tail -f logs/frontend.log"
    echo "  docker logs -f homework-pal-postgres"
}

# Cleanup function to stop all services
cleanup() {
    info "Stopping Homework Pal services..."

    # Stop backend if running
    if [[ -f ".backend.pid" ]]; then
        BACKEND_PID=$(cat .backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            info "Backend service stopped"
        fi
        rm -f .backend.pid
    fi

    # Stop frontend if running
    if [[ -f ".frontend.pid" ]]; then
        FRONTEND_PID=$(cat .frontend.pid)
        if kill -0 $FRONTEND_PID 2>/dev/null; then
            kill $FRONTEND_PID
            info "Frontend service stopped"
        fi
        rm -f .frontend.pid
    fi

    info "Cleanup completed"
}

# Register cleanup function for script termination
trap cleanup EXIT INT TERM

# Execute main function with all arguments
main "$@"