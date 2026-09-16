#!/bin/bash
# Quick restart script for F1 Predictor 2026
echo "Restarting F1 Predictor 2026..."

# Kill existing processes
echo "Stopping existing services..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
lsof -ti:5178 | xargs kill -9 2>/dev/null || true
sleep 1

# Start backend
echo "Starting backend on port 5000..."
cd /home/jackson11/projects/web/FORMULA_1_PREDICTOR_2026
nohup python3 backend/main.py > /tmp/f1_backend.log 2>&1 &
echo "Backend PID: $!"

# Wait for backend to start
echo "Waiting for backend to initialize..."
for i in {1..10}; do
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo "✓ Backend is ready!"
        break
    fi
    sleep 1
done

# Test endpoints
echo ""
echo "Testing API endpoints..."
echo -n "Races: "
curl -s http://localhost:5000/api/v1/races | python3 -c "import sys,json; print(f'{len(json.load(sys.stdin))} races')" 2>/dev/null || echo "FAILED"

echo -n "Drivers: "
curl -s http://localhost:5000/api/v1/drivers | python3 -c "import sys,json; print(f'{len(json.load(sys.stdin)[\"drivers\"])} drivers')" 2>/dev/null || echo "FAILED"

echo ""
echo "Backend is running! Start frontend manually with:"
echo "  cd frontend && npm run dev"
echo ""
echo "Then visit: http://localhost:5178"
