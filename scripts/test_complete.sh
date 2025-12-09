#!/bin/bash
# 完整测试脚本 - 启动服务、测试、然后停止服务

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# PIDs for cleanup
BACKEND_PID=""
FRONTEND_PID=""

# Logging functions
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Cleanup function
cleanup() {
    info "Stopping services..."

    if [[ -n "$BACKEND_PID" ]]; then
        kill $BACKEND_PID 2>/dev/null || true
        info "Backend stopped"
    fi

    if [[ -n "$FRONTEND_PID" ]]; then
        kill $FRONTEND_PID 2>/dev/null || true
        info "Frontend stopped"
    fi

    # Kill any remaining processes on ports
    lsof -ti:8001 | xargs kill -9 2>/dev/null || true
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true

    wait 2>/dev/null || true
}

# Register cleanup for script termination
trap cleanup EXIT INT TERM

# Check if virtual environment exists
check_requirements() {
    info "Checking requirements..."

    if [[ ! -d ".venv" ]]; then
        error "Virtual environment not found. Please run './init.sh' first."
    fi

    # Activate virtual environment
    source .venv/bin/activate

    # Check dependencies
    if ! python -c "import fastapi, chainlit, uvicorn" 2>/dev/null; then
        error "Required packages not installed. Please run './init.sh' first."
    fi

    success "Requirements check passed"
}

# Start services
start_services() {
    info "Starting Homework Pal services..."

    # Start backend
    info "Starting backend..."
    python -m homeworkpal.simple.api > logs/backend_test.log 2>&1 &
    BACKEND_PID=$!
    info "Backend started (PID: $BACKEND_PID)"

    # Wait for backend to be ready
    info "Waiting for backend to be ready..."
    for i in {1..30}; do
        if curl -f http://localhost:8001/health >/dev/null 2>&1; then
            success "Backend is ready"
            break
        elif [[ $i -eq 30 ]]; then
            error "Backend failed to start within 30 seconds"
        else
            sleep 1
        fi
    done

    # Start frontend
    info "Starting frontend..."
    chainlit run homeworkpal.simple.app --host 0.0.0.0 --port 8000 > logs/frontend_test.log 2>&1 &
    FRONTEND_PID=$!
    info "Frontend started (PID: $FRONTEND_PID)"

    # Wait for frontend to be ready
    info "Waiting for frontend to be ready..."
    for i in {1..45}; do
        if curl -f http://localhost:8000 >/dev/null 2>&1; then
            success "Frontend is ready"
            break
        elif [[ $i -eq 45 ]]; then
            error "Frontend failed to start within 45 seconds"
        else
            sleep 1
        fi
    done
}

# Run tests
run_tests() {
    echo ""
    echo "🧪 Testing Homework Pal Simple Version"
    echo "======================================"

    # Test backend API
    echo ""
    echo "🔧 Testing Backend API..."
    echo "----------------------------"

    # Test root endpoint
    echo "Testing root endpoint..."
    if curl -s http://localhost:8001/ | grep -q "Homework Pal API is running"; then
        success "✅ Root endpoint working"
    else
        error "❌ Root endpoint failed"
    fi

    # Test health check
    echo "Testing health endpoint..."
    if curl -s http://localhost:8001/health | grep -q "healthy"; then
        success "✅ Health endpoint working"
    else
        error "❌ Health endpoint failed"
    fi

    # Test status API
    echo "Testing status API..."
    if curl -s http://localhost:8001/api/v1/status | grep -q "operational"; then
        success "✅ Status API working"
    else
        error "❌ Status API failed"
    fi

    # Test frontend
    echo ""
    echo "📱 Testing Frontend..."
    echo "----------------------------"

    # Check frontend response
    echo "Testing frontend availability..."
    if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "200"; then
        success "✅ Frontend responding"
    else
        error "❌ Frontend not responding"
    fi

    echo ""
    echo "📋 Service Information"
    echo "======================"
    echo "Frontend (Browser): http://localhost:8000"
    echo "Backend API: http://localhost:8001"
    echo "API Docs: http://localhost:8001/docs"
    echo ""
    echo "🎉 All tests passed successfully!"
    echo ""
    echo "To test the frontend manually:"
    echo "1. Open http://localhost:8000 in your browser"
    echo "2. Try sending a message like '你好' or '帮助'"
    echo "3. Click the action buttons to test the interface"
    echo ""
    echo "📝 Logs are available in:"
    echo "- Backend: logs/backend_test.log"
    echo "- Frontend: logs/frontend_test.log"
}

# Main execution
main() {
    log "Starting comprehensive test..."

    check_requirements
    start_services
    run_tests

    echo ""
    info "Test completed successfully! Services will be stopped automatically."
}

# Run main function
main "$@"