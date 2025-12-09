#!/bin/bash
# 简单测试脚本 - 验证前后端基本功能
# 注意：此脚本假设服务已经启动。如果没有启动，请先运行 ./start_simple.sh

echo "🧪 Testing Homework Pal Simple Version"
echo "=================================="

# 检查服务是否运行
echo "🔍 Checking if services are running..."
if ! curl -s http://localhost:8001/health >/dev/null 2>&1; then
    echo "❌ Backend is not running. Please start services first:"
    echo "   ./start_simple.sh"
    exit 1
fi

if ! curl -s http://localhost:8000 >/dev/null 2>&1; then
    echo "❌ Frontend is not running. Please start services first:"
    echo "   ./start_simple.sh"
    exit 1
fi

echo "✅ Services are running"
echo ""

# 测试后端API
echo ""
echo "🔧 Testing Backend API..."
echo "----------------------------"

# 测试根端点
echo "Testing root endpoint..."
if curl -s http://localhost:8001/ | grep -q "Homework Pal API is running"; then
    echo "✅ Root endpoint working"
else
    echo "❌ Root endpoint failed"
fi

# 测试健康检查
echo "Testing health endpoint..."
if curl -s http://localhost:8001/health | grep -q "healthy"; then
    echo "✅ Health endpoint working"
else
    echo "❌ Health endpoint failed"
fi

# 测试状态API
echo "Testing status API..."
if curl -s http://localhost:8001/api/v1/status | grep -q "operational"; then
    echo "✅ Status API working"
else
    echo "❌ Status API failed"
fi

# 测试前端
echo ""
echo "📱 Testing Frontend..."
echo "----------------------------"

# 检查前端是否响应
echo "Testing frontend availability..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000 | grep -q "200"; then
    echo "✅ Frontend responding"
else
    echo "❌ Frontend not responding"
fi

echo ""
echo "📋 Service Information"
echo "======================"
echo "Frontend (Browser): http://localhost:8000"
echo "Backend API: http://localhost:8001"
echo "API Docs: http://localhost:8001/docs"
echo ""
echo "🎉 Basic functionality test completed!"
echo ""
echo "To test the frontend manually:"
echo "1. Open http://localhost:8000 in your browser"
echo "2. Try sending a message like '你好' or '帮助'"
echo "3. Click the action buttons to test the interface"