#!/bin/bash

# AIGoat Smart Startup Script
# Automatically detects if host Ollama is available and starts in appropriate mode

set -e

echo "🐐 AIGoat Local Development Setup"
echo "=================================="

# Function to check if Ollama is running on host
check_host_ollama() {
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        return 0  # Ollama is available
    else
        return 1  # Ollama is not available
    fi
}

# Function to check if required models are available
check_ollama_models() {
    echo "📝 Checking Ollama models..."
    
    if ! ollama list | grep -q "llava"; then
        echo "📥 Installing llava model..."
        ollama pull llava
    fi
    
    if ! ollama list | grep -q "llama3.1"; then
        echo "📥 Installing llama3.1 model..."
        ollama pull llama3.1
    fi
    
    echo "✅ Required models are available"
}

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env file from template..."
    cp env.example .env
fi

# Check for host Ollama
echo "🔍 Checking for host Ollama..."
if check_host_ollama; then
    echo "✅ Host Ollama detected on port 11434"
    echo "🚀 Starting AIGoat in HOST mode..."
    
    # Ensure required models are available
    check_ollama_models
    
    # Start in host mode (default)
    docker-compose up -d
    
    echo ""
    echo "✅ AIGoat started successfully!"
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:5000"
    echo "💾 MinIO Console: http://localhost:9001 (admin/admin)"
    echo "🤖 Using host Ollama: http://localhost:11434"
    
else
    echo "❌ No host Ollama detected on port 11434"
    echo "🐳 Starting AIGoat in CONTAINER mode..."
    echo "⏳ This will download Ollama and AI models (~9GB)..."
    
    # Start in container mode
    docker-compose --profile container-ollama up -d
    
    echo ""
    echo "✅ AIGoat started successfully!"
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔧 Backend API: http://localhost:5000"
    echo "💾 MinIO Console: http://localhost:9001 (admin/admin)"
    echo "🤖 Using container Ollama: http://localhost:11434"
    echo ""
    echo "⏳ First startup may take 10+ minutes to download AI models..."
fi

echo ""
echo "📊 Container status:"
docker-compose ps

echo ""
echo "📖 For more information, see README_LOCAL.md"
echo "🐛 Troubleshooting: docker-compose logs -f" 