#!/bin/bash
# ============================================================================
# Schedule Generator - Cloudflare Tunnel Startup Script (Linux/Mac)
# ============================================================================
# This script starts both the backend and Cloudflare Tunnel together.
# When you stop the tunnel (Ctrl+C), it automatically stops the backend too.
# ============================================================================

echo ""
echo "========================================"
echo " Schedule Generator - Cloudflare Tunnel"
echo "========================================"
echo ""

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "[ERROR] cloudflared is not installed!"
    echo ""
    echo "Please install it first:"
    echo "  brew install cloudflared  # macOS"
    echo "  # Or download from: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/"
    echo ""
    exit 1
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "========================================"
    echo " Tunnel stopped. Cleaning up..."
    echo "========================================"
    echo ""

    # Kill backend if it's running
    if [ ! -z "$BACKEND_PID" ]; then
        echo "Stopping backend server (PID: $BACKEND_PID)..."
        kill $BACKEND_PID 2>/dev/null
        wait $BACKEND_PID 2>/dev/null
    fi

    echo ""
    echo "Done! Both tunnel and backend have been stopped."
    echo ""
    exit 0
}

# Set up trap to cleanup on Ctrl+C or script exit
trap cleanup EXIT INT TERM

echo "[1/3] Starting backend server..."
echo ""

# Start backend in background
python run_app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if backend started successfully
if curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "[OK] Backend is running on http://localhost:8000"
    echo ""
else
    echo "[WARNING] Backend may not have started properly."
    echo "          Check if port 8000 is already in use."
    echo ""
fi

echo "[2/3] Starting Cloudflare Tunnel..."
echo ""
echo "Choose tunnel mode:"
echo "  1) Quick Tunnel (temporary URL, no config needed)"
echo "  2) Named Tunnel (permanent URL, requires setup)"
echo ""
read -p "Enter choice (1 or 2): " choice

if [ "$choice" = "1" ]; then
    echo ""
    echo "Starting quick tunnel..."
    echo "NOTE: The URL will change each time you restart!"
    echo ""
    echo "[3/3] Tunnel is starting..."
    echo "      Look for the URL below (https://xxx.trycloudflare.com)"
    echo ""
    echo "========================================"
    echo ""
    cloudflared tunnel --url http://localhost:8000
elif [ "$choice" = "2" ]; then
    echo ""
    echo "Starting named tunnel..."
    echo "NOTE: Make sure you've run 'cloudflared tunnel create schedule-generator' first!"
    echo ""
    echo "[3/3] Tunnel is starting..."
    echo ""
    echo "========================================"
    echo ""
    cloudflared tunnel run schedule-generator
else
    echo "Invalid choice. Defaulting to quick tunnel..."
    echo ""
    cloudflared tunnel --url http://localhost:8000
fi

# Cleanup will happen automatically via trap
