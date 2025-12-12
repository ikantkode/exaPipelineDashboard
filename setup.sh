#!/bin/bash

# Construction AI Dashboard Setup Script

set -e

echo "🏗️ Construction AI Dashboard Setup"
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if pipeline network exists
if ! docker network ls | grep -q "exapipeline_pipeline-network"; then
    echo "⚠️  Pipeline network not found. Make sure your pipeline is running."
    echo "   Run this from your pipeline directory: docker-compose up -d"
    read -p "Continue anyway? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔧 Creating .env file..."
    cat > .env << 'ENVEOF'
# Dashboard Settings
PIPELINE_API_URL=http://host.docker.internal:8000
PIPELINE_DATA_DIR=/pipeline_data

# Streamlit Settings
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_THEME_BASE=dark
ENVEOF
    echo "✅ Created .env file"
fi

# Build Docker image
echo "🐳 Building Docker image..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Dashboard available at: http://localhost:8501"
echo ""
echo "📋 Services status:"
echo "   Dashboard:      http://localhost:8501"
echo "   Pipeline API:   http://localhost:8001"
echo "   Flower Monitor: http://localhost:5555"
echo ""
echo "🔧 To stop services:"
echo "   docker-compose down"
echo ""
echo "🔍 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🔄 To restart:"
echo "   docker-compose restart"
echo ""
echo "🏗️ Happy building!"
