#!/bin/bash
# Final verification that everything is working after auth removal

echo "=========================================="
echo "F1 Predictor 2026 - Final Status Check"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd /home/jackson11/projects/web/FORMULA_1_PREDICTOR_2026

# Check backend
echo -e "${YELLOW}Backend Status:${NC}"
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Backend running on port 5000${NC}"
    
    # Test endpoints
    echo ""
    echo "Testing API endpoints..."
    
    RACES=$(curl -s http://localhost:5000/api/v1/races | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Races endpoint: $RACES races${NC}"
    else
        echo -e "${RED}✗ Races endpoint failed${NC}"
    fi
    
    DRIVERS=$(curl -s http://localhost:5000/api/v1/drivers | python3 -c "import sys,json; print(len(json.load(sys.stdin)['drivers']))" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Drivers endpoint: $DRIVERS drivers${NC}"
    else
        echo -e "${RED}✗ Drivers endpoint failed${NC}"
    fi
    
    STANDINGS=$(curl -s http://localhost:5000/api/v1/standings/drivers | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('standings', [])))" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Standings endpoint: $STANDINGS drivers${NC}"
    else
        echo -e "${RED}✗ Standings endpoint failed${NC}"
    fi
else
    echo -e "${RED}✗ Backend NOT running${NC}"
    echo "Starting backend..."
    nohup python3 backend/main.py > /tmp/f1_backend.log 2>&1 &
    sleep 3
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend started successfully${NC}"
    else
        echo -e "${RED}✗ Backend failed to start${NC}"
        tail -20 /tmp/f1_backend.log
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Frontend Status:${NC}"
if curl -s http://localhost:5178/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend running on port 5178${NC}"
else
    echo -e "${RED}✗ Frontend NOT running${NC}"
    echo ""
    echo "To start frontend, run:"
    echo "  cd frontend && npm run dev"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}System Status Summary${NC}"
echo "=========================================="
echo ""
echo "Backend API: $(curl -s http://localhost:5000/health | python3 -c 'import sys,json; print("RUNNING ✓")' 2>/dev/null || echo 'NOT RUNNING ✗')"
echo "Races Data: ${RACES:-N/A} races available"
echo "Drivers Data: ${DRIVERS:-N/A} drivers available"
echo "Standings Data: ${STANDINGS:-N/A} drivers in standings"
echo ""
echo "Frontend: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:5178/ 2>/dev/null | grep -q 200 && echo 'RUNNING ✓' || echo 'NOT RUNNING ✗')"
echo ""
echo "=========================================="
echo ""
echo "Access the application at: http://localhost:5178"
echo ""
echo "If frontend is not running, start it with:"
echo "  cd /home/jackson11/projects/web/FORMULA_1_PREDICTOR_2026/frontend"
echo "  npm run dev"
echo ""
echo "Then refresh your browser (Ctrl+Shift+R)"
