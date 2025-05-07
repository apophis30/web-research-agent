# Web Research Agent Backend

A FastAPI-based backend service that provides web research capabilities, utilizing Redis for caching and data storage.

## Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose
- Git

## Local Development Setup

You have two options for local development:

### Option 1: Using Docker Compose (Recommended)

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd web-research-agent
   ```

2. **Set Up Environment Variables**
   ```bash
   cp .example.env .env
   ```
   Update the `.env` file with your credentials:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `REDIS_URL`: Redis connection URL (default: redis://redis:6379)
   - `SERPER_API_KEY_1`: Your Serper API key
   - `SERP_API_KEY`: Your SERP API key

3. **Start the Application**
   ```bash
   docker-compose up -d
   ```
   The API will be available at http://localhost:8000

### Option 2: Manual Setup (Redis in Docker, App Locally)

1. **Clone and Set Up Python Environment**
   ```bash
   git clone <repository-url>
   cd web-research-agent
   python -m venv .venv
   
   # Activate virtual environment
   # On Windows:
   .venv\Scripts\activate
   # On Unix or MacOS:
   source .venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Redis Container**
   ```bash
   docker run --name redis-cache -p 6379:6379 -d redis:latest
   ```

4. **Configure Environment**
   ```bash
   cp .example.env .env
   ```
   Update the `.env` file with your credentials (same as Option 1)

5. **Run the Application**
   ```bash
   uvicorn routers.app:app --host 0.0.0.0 --port 8000
   ```

## AWS EC2 Deployment

### 1. Launch EC2 Instance
- Use t2.micro instance (Free Tier eligible)
- Ubuntu Server 22.04 LTS
- Security Group Configuration:
  - Port 22 (SSH)
  - Port 8000 (API)
- 8GB EBS volume (Free Tier eligible)

### 2. Instance Setup
```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker and Docker Compose
sudo apt-get install -y docker.io
sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in
```

### 3. Deploy Application
```bash
# Clone repository
git clone <repository-url>
cd web-research-agent

# Create .env file
cat > .env << EOL
OPENAI_API_KEY=your_api_key_here
REDIS_URL=redis://redis:6379
SERPER_API_KEY_1=your_serper_key_here
SERP_API_KEY=your_serp_key_here
EOL

# Start application
docker-compose up -d
```

### 4. Verify Deployment
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs -f

# Test API
curl http://localhost:8000/
```

## Maintenance

### Viewing Logs
```bash
docker-compose logs -f
```

### Updating Application
```bash
git pull
docker-compose down
docker-compose up -d --build
```

### Stopping Application
```bash
docker-compose down
```

## Resource Management

### Free Tier Considerations
- t2.micro instance: 1 vCPU, 1GB RAM
- Container resource limits:
  - Web Research Agent: 0.5 CPU, 512MB RAM
  - Redis: 0.3 CPU, 256MB RAM

### Monitoring
1. Set up CloudWatch monitoring (free tier)
2. Monitor CPU and memory usage
3. Set up alarms for resource utilization
4. Monitor application logs

## Security Best Practices
1. Use AWS Security Groups to restrict access
2. Keep API keys secure in .env file
3. Regular system and dependency updates

## Troubleshooting

### Common Issues
1. **Redis Connection Issues**
   ```bash
   docker ps | grep redis
   ```

2. **Environment Variables**
   ```bash
   cat .env
   ```

3. **Dependencies**
   ```bash
   pip list
   ```

4. **Application Logs**
   ```bash
   docker-compose logs -f
   ```

## Project Structure
```
web-research-agent/
├── assets/           # Images for proper documentation
├── routers/          # FastAPI route handlers
├── config/           # Configuration files
├── scripts/          # Utility scripts
├── test/             # Test files
├── main.py           # Main FastAPI application
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
``` 