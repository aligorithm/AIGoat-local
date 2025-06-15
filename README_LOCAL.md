# AIGoat Local Development Setup

This is a local development version of AIGoat that runs entirely on your local machine without requiring AWS services.

## 🏗️ Architecture

- **Frontend**: Next.js React application
- **Backend**: Flask API with integrated ML services  
- **Database**: PostgreSQL
- **Storage**: MinIO (S3-compatible)
- **AI Runtime**: Ollama (auto-detects host vs container)

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 4GB RAM available
- 10GB free disk space (for AI models if using container mode)

### 1. One-Command Startup (Recommended)

```bash
# Clone and start with smart detection
git clone https://github.com/aligorithm/AIGoat-local.git
cd AIGoat-local
./start-aigoat.sh
```

The script will:
- ✅ **Auto-detect** if you have Ollama running locally
- 🏠 **Host Mode**: Use your existing Ollama (faster, saves resources)
- 🐳 **Container Mode**: Start Ollama in Docker if none detected
- 📥 **Auto-install** required models if missing

### 2. Manual Setup

```bash
# Copy environment file
cp env.example .env

# Option A: Use host Ollama (if you have it installed)
docker-compose up -d

# Option B: Use container Ollama (downloads models)
docker-compose --profile container-ollama up -d
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **MinIO Console**: http://localhost:9001 (admin/admin)
- **Ollama API**: http://localhost:11434

## 🤖 Ollama Modes

### Host Mode (Recommended)
- **When**: You have Ollama installed on your system
- **Benefits**: Faster startup, less resource usage, persistent models
- **How**: Automatically detected by `start-aigoat.sh` or use `docker-compose up -d`

### Container Mode
- **When**: No local Ollama installation
- **Benefits**: Everything in containers, no host dependencies
- **How**: Use `docker-compose --profile container-ollama up -d`
- **Note**: First run downloads ~9GB of models

### Manual Mode Switching

```bash
# Force container mode even if host Ollama exists
docker-compose --profile container-ollama up -d

# Switch back to host mode
docker-compose down
docker-compose up -d

# Check current mode
docker-compose ps
```

## 🔧 Configuration

### AI Provider Settings

Edit `.env` to switch between Ollama and OpenAI:

```bash
# Use local Ollama (default)
AI_PROVIDER=ollama

# Or use OpenAI
AI_PROVIDER=openai
OPENAI_API_KEY=your-api-key-here
```

### Ollama Endpoint Configuration

```bash
# Host mode (default)
OLLAMA_ENDPOINT=http://host.docker.internal:11434

# Container mode
OLLAMA_ENDPOINT=http://ollama:11434
```

### Model Configuration

```bash
# Ollama models (adjust as needed)
OLLAMA_MODEL_IMAGE=llava      # For image analysis
OLLAMA_MODEL_TEXT=llama3.1    # For text processing

# OpenAI models
OPENAI_MODEL_IMAGE=gpt-4-vision-preview
OPENAI_MODEL_TEXT=gpt-4-turbo
```

## 🎯 Challenges

The local setup preserves all three original AI security challenges:

### Challenge 1: Supply Chain Attack
- **Endpoint**: `/api/analyze-photo`
- **Goal**: Exploit file upload vulnerabilities
- **Login**: Not required

### Challenge 2: Data Poisoning Attack  
- **Endpoint**: `/api/recommendations`
- **Goal**: Manipulate recommendations to show "Orca Doll"
- **Login**: Required (`babyshark` / `doodoo123`)

### Challenge 3: Output Integrity Attack
- **Endpoint**: `/products/{id}/comments`
- **Goal**: Bypass content filter to post "pwned"
- **Login**: Not required

## 🔍 Hints

Access hints at:
- `http://localhost:5000/hints/challenge1/{1,2,3}`
- `http://localhost:5000/hints/challenge2/{1,2,3}`  
- `http://localhost:5000/hints/challenge3/{1,2,3}`

## 🛠️ Development

### Hot Reload

Both frontend and backend support hot reload:

```bash
# Edit files in ./frontend/ or ./backend/
# Changes will be automatically reflected
```

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f ollama  # Only in container mode
```

### Database Access

```bash
# Access PostgreSQL directly
docker-compose exec postgres psql -U pos_user -d postgres
```

### Storage Access

- **MinIO Console**: http://localhost:9001
- **Credentials**: minioadmin / minioadmin
- **Buckets**: supply-chain-bucket, data-poisoning-bucket, uploads-bucket

## 🐛 Troubleshooting

### Common Issues

**Port 11434 already in use:**
```bash
# Check what's using the port
sudo lsof -i :11434

# If it's host Ollama, use host mode (default)
docker-compose up -d

# If it's something else, stop it or use different port
```

**Services won't start:**
```bash
# Check system resources
docker system df
docker system prune  # Free up space

# Restart services
docker-compose down
docker-compose up -d
```

**Models not downloading (container mode):**
```bash
# Check Ollama logs
docker-compose logs ollama-init

# Manually pull models
docker-compose exec ollama ollama pull llava
docker-compose exec ollama ollama pull llama3.1
```

**Database connection errors:**
```bash
# Check PostgreSQL status
docker-compose logs postgres

# Reset database
docker-compose down -v  # WARNING: This deletes all data
docker-compose up -d
```

**AI responses not working:**
```bash
# Check AI provider configuration
docker-compose logs backend | grep "ML Service"

# Test Ollama directly
curl http://localhost:11434/api/tags

# For OpenAI, verify API key in .env
```

### Performance Issues

**High RAM usage:**
- Container mode: Ollama models use 2-6GB RAM each
- Host mode: Uses your existing Ollama installation
- Consider using OpenAI API for lower resource usage

**Slow responses:**
- First AI requests are slower (model loading)
- Subsequent requests should be faster
- Host mode is generally faster than container mode

## 📋 Command Reference

### Startup Commands
```bash
# Smart startup (recommended)
./start-aigoat.sh

# Manual host mode
docker-compose up -d

# Manual container mode
docker-compose --profile container-ollama up -d

# Stop everything
docker-compose down
```

### Mode Detection
```bash
# Check if Ollama is running locally
curl http://localhost:11434/api/tags

# Check current Docker mode
docker-compose ps

# Check Ollama models
ollama list  # Host mode
docker-compose exec ollama ollama list  # Container mode
```

### Development Commands
```bash
# Rebuild containers
docker-compose up --build -d

# View live logs
docker-compose logs -f

# Reset everything (⚠️ deletes data)
docker-compose down -v
```

## 📦 Production Deployment

For production deployment, create a separate `docker-compose.prod.yml`:

```yaml
# Example production overrides
version: '3.8'
services:
  backend:
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=0
  
  frontend:
    environment:
      - NODE_ENV=production
    command: ["yarn", "start"]
```

## 🔄 Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose down
docker-compose up --build -d
```

## 🧹 Cleanup

```bash
# Stop all services
docker-compose down

# Remove all data (WARNING: Irreversible)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## 📝 Notes

- **Smart Detection**: Automatically chooses host vs container Ollama
- **Resource Friendly**: Host mode saves RAM and disk space
- **No Vendor Lock-in**: Easy switching between Ollama and OpenAI
- **Educational Focus**: Preserves all security vulnerabilities for learning
- **Production Ready**: Can be adapted for production deployment

## 🆘 Support

If you encounter issues:

1. **Try the smart startup**: `./start-aigoat.sh`
2. **Check the logs**: `docker-compose logs -f`
3. **Verify system requirements** (RAM, disk space)
4. **Ensure ports are available** (3000, 5000, 9000, 9001, 11434)
5. **Try container mode** if host mode fails

For more help, refer to the original AIGoat documentation or create an issue in the repository. 