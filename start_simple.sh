#!/bin/bash
# 简化版本的启动脚本 - 暂时忽略数据库，专注于前后端启动

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
SKIP_FRONTEND=false
LOG_FILE="simple_start.log"

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
Homework Pal Simple Start Script

Usage: $0 [OPTIONS]

Options:
    --no-frontend         Skip frontend service startup
    -h, --help          Show this help message

Description:
    This script starts the simplified version of Homework Pal without database connections.
    It focuses on getting the frontend and backend services running for testing.

Services:
    - Backend (FastAPI): http://localhost:8001
    - Frontend (Chainlit): http://localhost:8000

Examples:
    $0                    # Start both frontend and backend
    $0 --no-frontend      # Start backend only

EOF
}

# Check system requirements
check_requirements() {
    info "Checking system requirements..."

    # Check if virtual environment exists
    if [[ ! -d ".venv" ]]; then
        error "Virtual environment not found. Please run './init.sh' first to set up the environment."
    fi

    # Activate virtual environment
    info "Activating virtual environment..."
    source .venv/bin/activate

    # Check if required packages are installed
    if ! python -c "import fastapi, chainlit, uvicorn" 2>/dev/null; then
        error "Required packages not installed. Please run './init.sh' first."
    fi

    success "System requirements check passed"
}

# Start backend services
start_backend() {
    info "Starting FastAPI backend (simplified version)..."

    # Use the simplified version without database dependencies
    uvicorn main_simple:app --host 0.0.0.0 --port 8001 --reload > backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > .backend.pid

    success "Backend service started (PID: $BACKEND_PID)"
}

# Start frontend services
start_frontend() {
    if [[ "$SKIP_FRONTEND" == false ]]; then
        info "Starting Chainlit frontend (simplified version)..."

        # Use the simplified version without database dependencies
        chainlit run app_simple.py --host 0.0.0.0 --port 8000 > frontend.log 2>&1 &
        FRONTEND_PID=$!
        echo $FRONTEND_PID > .frontend.pid

        success "Frontend service started (PID: $FRONTEND_PID)"
    else
        info "Skipping frontend startup (--no-frontend flag)"
    fi
}

# Perform health checks
health_check() {
    info "Performing health checks..."

    # Check backend health
    info "Checking backend health..."
    for i in {1..30}; do
        if curl -f http://localhost:8001/health > /dev/null 2>&1; then
            success "Backend health check passed"
            break
        elif [[ $i -eq 30 ]]; then
            error "Backend health check failed after 30 seconds"
        else
            sleep 1
        fi
    done

    # Check frontend health if running
    if [[ "$SKIP_FRONTEND" == false ]]; then
        info "Checking frontend health..."
        for i in {1..30}; do
            if curl -f http://localhost:8000 > /dev/null 2>&1; then
                success "Frontend health check passed"
                break
            elif [[ $i -eq 30 ]]; then
                error "Frontend health check failed after 30 seconds"
            else
                sleep 1
            fi
        done
    fi
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

# Main execution function
main() {
    log "Starting Homework Pal simplified services..."

    # Parse command line arguments
    parse_args "$@"

    # Check system requirements
    check_requirements

    # Start services
    start_backend
    start_frontend

    # Health checks
    health_check

    success "Homework Pal simplified services started successfully!"

    echo ""
    echo "🌰 Homework Pal is now running!"
    echo "📱 Frontend (Browser): http://localhost:8000"
    echo "🔧 Backend API: http://localhost:8001"
    echo "📊 API Docs: http://localhost:8001/docs"
    echo ""
    echo "To stop services:"
    echo "  Press Ctrl+C or run: kill \$(cat .backend.pid 2>/dev/null) \$(cat .frontend.pid 2>/dev/null)"
    echo ""
    echo "To view logs:"
    echo "  tail -f backend.log"
    echo "  tail -f frontend.log"
    echo ""

    # Keep script running
    info "Services are running. Press Ctrl+C to stop."
    while true; do
        sleep 5
        # Check if services are still running
        if [[ -f ".backend.pid" ]]; then
            BACKEND_PID=$(cat .backend.pid)
            if ! kill -0 $BACKEND_PID 2>/dev/null; then
                warning "Backend service has stopped unexpectedly"
                break
            fi
        fi

        if [[ -f ".frontend.pid" && "$SKIP_FRONTEND" == false ]]; then
            FRONTEND_PID=$(cat .frontend.pid)
            if ! kill -0 $FRONTEND_PID 2>/dev/null; then
                warning "Frontend service has stopped unexpectedly"
                break
            fi
        fi
    done
}

# Execute main function with all arguments
main "$@"