#!/bin/bash
echo "Starting the application..."

# 1. Navigate to application folder
cd /home/ubuntu/compiler-app

# 2. Find and kill any old process running on port 5000
OLD_PID=$(lsof -t -i:5000)
if [ ! -z "$OLD_PID" ]; then
    echo "Killing old process running on port 5000 (PID: $OLD_PID)"
    kill -9 $OLD_PID
fi

# 3. Set up and activate a Python virtual environment (best practice to avoid system environment breaks)
python3 -m venv venv
source venv/bin/activate

# 4. Install requirements in the virtual environment
pip install --upgrade pip
pip install -r requirements.txt

# 5. Start the application in the background and redirect logs
echo "Launching Flask application via nohup..."
nohup python3 app.py > app.log 2>&1 &

echo "Application started successfully."
