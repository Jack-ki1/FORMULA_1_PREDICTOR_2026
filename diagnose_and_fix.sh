#!/bin/bash
# Diagnostic and Fix Script for F1 Predictor 2026
# This script checks and fixes common issues with races, calendar, drivers not appearing

echo "=========================================="
echo "F1 Predictor 2026 - Diagnostic & Fix Tool"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd /home/jackson11/projects/web/FORMULA_1_PREDICTOR_2026

# Step 1: Check if backend is running
echo -e "${YELLOW}Step 1: Checking backend server...${NC}"
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend is running on port 5000${NC}"
else
    echo -e "${RED}✗ Backend is NOT running${NC}"
    echo "Starting backend server..."
    
    # Kill any existing processes on port 5000
    lsof -ti:5000 | xargs kill -9 2>/dev/null || true
    
    # Start backend in background
    nohup python3 backend/main.py > /tmp/f1_backend.log 2>&1 &
    BACKEND_PID=$!
    echo "Backend started with PID: $BACKEND_PID"
    
    # Wait for startup
    echo "Waiting for backend to initialize..."
    sleep 5
    
    # Verify it started
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend started successfully${NC}"
    else
        echo -e "${RED}✗ Backend failed to start. Check logs:${NC}"
        tail -50 /tmp/f1_backend.log
        exit 1
    fi
fi

# Step 2: Test API endpoints
echo ""
echo -e "${YELLOW}Step 2: Testing API endpoints...${NC}"

echo -n "Testing /api/v1/races... "
RACES_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/v1/races)
if [ "$RACES_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ OK (HTTP $RACES_RESPONSE)${NC}"
    RACES_COUNT=$(curl -s http://localhost:5000/api/v1/races | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
    echo "   Found $RACES_COUNT races"
else
    echo -e "${RED}✗ FAILED (HTTP $RACES_RESPONSE)${NC}"
fi

echo -n "Testing /api/v1/drivers... "
DRIVERS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/v1/drivers)
if [ "$DRIVERS_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ OK (HTTP $DRIVERS_RESPONSE)${NC}"
    DRIVERS_COUNT=$(curl -s http://localhost:5000/api/v1/drivers | python3 -c "import sys,json; print(len(json.load(sys.stdin)['drivers']))")
    echo "   Found $DRIVERS_COUNT drivers"
else
    echo -e "${RED}✗ FAILED (HTTP $DRIVERS_RESPONSE)${NC}"
fi

echo -n "Testing /api/v1/standings/drivers... "
STANDINGS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/api/v1/standings/drivers)
if [ "$STANDINGS_RESPONSE" = "200" ]; then
    echo -e "${GREEN}✓ OK (HTTP $STANDINGS_RESPONSE)${NC}"
else
    echo -e "${RED}✗ FAILED (HTTP $STANDINGS_RESPONSE)${NC}"
fi

# Step 3: Check frontend
echo ""
echo -e "${YELLOW}Step 3: Checking frontend server...${NC}"
if curl -s http://localhost:5178/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is running on port 5178${NC}"
else
    echo -e "${RED}✗ Frontend is NOT running${NC}"
    echo "Please start frontend manually:"
    echo "  cd frontend && npm run dev"
fi

# Step 4: Check API client configuration
echo ""
echo -e "${YELLOW}Step 4: Checking API client configuration...${NC}"
if grep -q "f1_access_token" frontend/src/api/client.ts; then
    echo -e "${RED}✗ API client still has auth token logic${NC}"
    echo "This should have been removed. Please check the file."
else
    echo -e "${GREEN}✓ API client is clean (no auth tokens)${NC}"
fi

# Step 5: Performance check
echo ""
echo -e "${YELLOW}Step 5: Performance check...${NC}"
echo -n "Races endpoint response time: "
TIME_START=$(date +%s%N)
curl -s http://localhost:5000/api/v1/races > /dev/null
TIME_END=$(date +%s%N)
ELAPSED=$(( (TIME_END - TIME_START) / 1000000 ))
if [ $ELAPSED -lt 100 ]; then
    echo -e "${GREEN}${ELAPSED}ms (excellent)${NC}"
elif [ $ELAPSED -lt 500 ]; then
    echo -e "${YELLOW}${ELAPSED}ms (acceptable)${NC}"
else
    echo -e "${RED}${ELAPSED}ms (too slow!)${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Diagnostic complete!${NC}"
echo "=========================================="
echo ""
echo "If all tests passed, refresh your browser (Ctrl+Shift+R)"
echo "If tests failed, check the backend logs:"
echo "  tail -f /tmp/f1_backend.log"
