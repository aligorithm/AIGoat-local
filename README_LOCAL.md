# AIGoat Local Development Setup

This is a local development version of AIGoat that runs entirely on your local machine without requiring AWS services.

## 🏗️ Architecture

- **Frontend**: Next.js React application
- **Backend**: Flask API with integrated ML services  
- **Database**: PostgreSQL
- **Storage**: MinIO (S3-compatible)
- **AI Runtime**: Ollama (with OpenAI as alternative)

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- At least 4GB RAM available
- 10GB free disk space (for AI models)

### 1. Setup Environment

```bash
# Clone the repository
git clone <repository-url>
cd AIGoat

# Copy environment file
cp env.example .env

# Edit .env file with your preferences (optional)
# Default settings work out of the box
```

### 2. Start All Services

```bash
# Start the entire stack
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Wait for Initialization

The first startup will take several minutes as it:
- Downloads AI models (llava ~4GB, llama3.1 ~5GB)
- Initializes the database
- Sets up storage buckets

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **MinIO Console**: http://localhost:9001 (admin/admin)
- **Ollama API**: http://localhost:11434

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
docker-compose logs -f ollama
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

**Services won't start:**
```bash
# Check system resources
docker system df
docker system prune  # Free up space

# Restart services
docker-compose down
docker-compose up -d
```

**Models not downloading:**
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
- Ollama models use 2-6GB RAM each
- Consider using smaller models or OpenAI API

**Slow responses:**
- First AI requests are slower (model loading)
- Subsequent requests should be faster

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

- This setup is designed for local learning and testing
- The vulnerabilities are intentionally preserved for educational purposes
- For production use, additional security measures should be implemented
- AI model responses may vary based on the provider and model used

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify system requirements (RAM, disk space)
3. Ensure all environment variables are set correctly
4. Try restarting: `docker-compose restart`

For more help, refer to the original AIGoat documentation or create an issue in the repository. 