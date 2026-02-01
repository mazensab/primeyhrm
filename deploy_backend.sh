#!/bin/bash
set -e

echo "🚀 Deploying Primey HR Backend..."

cd /var/www/primeyhr

echo "📥 Pulling latest code from GitHub..."
git pull origin main

echo "🐍 Activating virtualenv..."
source venv/bin/activate

if [ -f requirements.txt ]; then
  echo "📦 Installing Python dependencies..."
  pip install -r requirements.txt
fi

echo "🗄️ Applying database migrations..."
python manage.py migrate --noinput

echo "🎨 Collecting static files..."
python manage.py collectstatic --noinput

echo "♻️ Restarting backend service..."
sudo systemctl restart primeyhr-backend

echo "✅ Backend deployment completed successfully."
