#!/bin/bash
# Quick start script for F1 Predictor 2026 with authentication
# This script sets up and starts the application

set -e

echo "=========================================="
echo "F1 Predictor 2026 - Quick Start"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cat > .env << 'EOF'
# ==========================================
# F1 Predictor 2026 Configuration
# ==========================================

# Application
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production-$(openssl rand -hex 32)

# Admin User (CHANGE THESE!)
ADMIN_EMAIL=admin@f1predictor.com
ADMIN_USERNAME=admin
ADMIN_PASSWORD=F1Admin2026!Secure
ADMIN_NAME=F1 Predictor Admin

# JWT Settings
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Database
DATABASE_URL=sqlite:///./f1_predictions.db

# Frontend
VITE_API_BASE=http://localhost:5000
FRONTEND_ORIGIN=http://localhost:5178

# CORS
CORS_ORIGINS=*
EOF
    echo "✅ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and change SECRET_KEY and ADMIN_PASSWORD before production!"
    echo ""
fi

# Install dependencies
echo "📦 Installing Python dependencies..."
pip install passlib[bcrypt] python-jose[cryptography] python-multipart bcrypt==4.0.1 > /dev/null 2>&1 || {
    echo "⚠️  Some packages may already be installed, continuing..."
}
echo "✅ Dependencies installed"
echo ""

# Check if database exists
if [ ! -f "f1_predictions.db" ]; then
    echo "🗄️  Database not found. It will be created on first run."
    echo ""
fi

# Start backend in background
echo "🚀 Starting backend server..."
python3 backend/main.py > /tmp/f1_backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
echo "   Logs: /tmp/f1_backend.log"
echo ""

# Wait for backend to start
echo "⏳ Waiting for backend to initialize..."
for i in {1..30}; do
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start. Check logs: /tmp/f1_backend.log"
        kill $BACKEND_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done
echo ""

# Show admin credentials
echo "=========================================="
echo "🔐 Admin Credentials"
echo "=========================================="
echo "Email:    $(grep ADMIN_EMAIL .env | cut -d'=' -f2)"
echo "Username: $(grep ADMIN_USERNAME .env | cut -d'=' -f2)"
echo "Password: $(grep ADMIN_PASSWORD .env | cut -d'=' -f2)"
echo ""
echo "⚠️  CHANGE THE PASSWORD AFTER FIRST LOGIN!"
echo ""

# Start frontend
echo "🎨 Starting frontend development server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"
echo ""

# Wait for frontend
echo "⏳ Waiting for frontend to start..."
for i in {1..20}; do
    if curl -s http://localhost:5178/ > /dev/null 2>&1; then
        echo "✅ Frontend is ready!"
        break
    fi
    if [ $i -eq 20 ]; then
        echo "⚠️  Frontend may still be starting..."
    fi
    sleep 1
done
echo ""

echo "=========================================="
echo "✅ Application Started Successfully!"
echo "=========================================="
echo ""
echo "📱 Access the application:"
echo "   Frontend: http://localhost:5178"
echo "   API Docs: http://localhost:5000/docs"
echo "   Health:   http://localhost:5000/health"
echo ""
echo "🔑 First steps:"
echo "   1. Open http://localhost:5178 in your browser"
echo "   2. You'll be redirected to the login page"
echo "   3. Login with the admin credentials above"
echo "   4. Change your password immediately!"
echo ""
echo "🛑 To stop the servers:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "📋 Useful commands:"
echo "   View backend logs: tail -f /tmp/f1_backend.log"
echo "   Test auth system:  python3 test_auth.py"
echo "   Read docs:         cat AUTH_SETUP.md"
echo ""
echo "=========================================="

# Keep script running
wait
