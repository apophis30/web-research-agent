# Masonry Assignment

This project is a web application that combines FastAPI backend with a Next.js frontend, using Redis for caching and data storage.

## Prerequisites

- Python 3.8 or higher
- Node.js and npm
- Docker and Docker Compose
- Git

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd masonry-assignment
```

### 2. Set Up Python Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On Unix or MacOS:
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend/masonry-frontend-next
npm install
cd ../..
```

### 4. Set Up Redis using Docker

```bash
# Pull and run Redis container
docker run --name redis-cache -p 6379:6379 -d redis:latest
```

### 5. Environment Configuration

1. Copy the example environment file:
```bash
cp .example.env .env
```

2. Update the `.env` file with your credentials:
- `OPENAI_API_KEY`: Your OpenAI API key
- `REDIS_URL`: Redis connection URL (default: redis://localhost:6379)
- `SERPER_API_KEY_1`: Your Serper API key
- `SERP_API_KEY`: Your SERP API key

### 6. Running the Application

You have two options to run the application:

#### Option 1: Using launch.py (Recommended)
This will start both the FastAPI backend and Next.js frontend automatically:

```bash
python launch.py
```

The script will:
- Start the FastAPI backend on port 8000
- Start the Next.js frontend on port 3000
- Handle graceful shutdown of both services
- Provide combined logging output

#### Option 2: Manual Start
If you prefer to run the services separately:

1. Start the FastAPI backend:
```bash
uvicorn routers.app:app --host 0.0.0.0 --port 8000
```

2. In a separate terminal, start the Next.js frontend:
```bash
cd frontend/masonry-frontend-next
npm run dev
```

The application will be accessible at:
- Backend API: http://localhost:8000
- Frontend: http://localhost:3000

## Project Structure

- `frontend/masonry-frontend-next/`: Contains the Next.js frontend application
- `routers/`: FastAPI route handlers
- `config/`: Configuration files
- `scripts/`: Utility scripts
- `test/`: Test files
- `main.py`: Main FastAPI application entry point
- `launch.py`: Application launcher script

## Additional Notes

- The Redis instance runs on port 6379 by default
- Make sure all required API keys are properly configured in the `.env` file
- The application uses async operations for better performance
- Redis is used for caching and temporary data storage

## Troubleshooting

If you encounter any issues:

1. Ensure Redis is running:
```bash
docker ps | grep redis
```

2. Check if all environment variables are properly set:
```bash
cat .env
```

3. Verify all dependencies are installed:
```bash
# Check Python dependencies
pip list

# Check Node.js dependencies
cd frontend/masonry-frontend-next
npm list
```

4. Check the application logs for any error messages

## AWS EC2 Free Tier Deployment Guide

### Prerequisites
1. An AWS account
2. AWS CLI installed and configured
3. Docker and Docker Compose installed on your EC2 instance

### Deployment Steps

1. **Launch an EC2 Instance (Free Tier)**
   - Launch a t2.micro instance (eligible for free tier)
   - Use Ubuntu Server 22.04 LTS
   - Configure security group to allow inbound traffic on:
     - Port 22 (SSH)
     - Port 8000 (API)
   - Use a key pair for SSH access
   - Use the default 8GB EBS volume (free tier eligible)

2. **Install Dependencies on EC2**
   ```bash
   # Update system
   sudo apt-get update
   sudo apt-get upgrade -y

   # Install Docker
   sudo apt-get install -y docker.io

   # Install Docker Compose
   sudo curl -L "https://github.com/docker/compose/releases/download/v2.24.1/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose

   # Add your user to docker group
   sudo usermod -aG docker $USER
   # Log out and log back in for group changes to take effect
   ```

3. **Deploy the Application**
   ```bash
   # Clone your repository
   git clone <your-repository-url>
   cd web-research-agent

   # Create .env file with your API keys
   cat > .env << EOL
   OPENAI_API_KEY=your_api_key_here
   REDIS_URL=redis://redis:6379
   EOL

   # Build and start containers
   docker-compose up -d
   ```

4. **Verify Deployment**
   - Check if containers are running:
     ```bash
     docker-compose ps
     ```
   - Test the API:
     ```bash
     curl http://localhost:8000/
     ```

### Free Tier Considerations

1. **Resource Limits**
   - t2.micro instance has 1 vCPU and 1GB RAM
   - Docker containers are configured with resource limits:
     - Web Research Agent: 0.5 CPU, 512MB RAM
     - Redis: 0.3 CPU, 256MB RAM

2. **Cost Optimization**
   - Use t2.micro instance (free tier eligible)
   - Use 8GB EBS volume (free tier eligible)
   - Monitor usage to stay within free tier limits
   - Set up CloudWatch alarms for cost monitoring

3. **Performance Tips**
   - Keep the application lightweight
   - Monitor memory usage
   - Use Redis for caching to reduce API calls
   - Implement proper error handling and retries

### Maintenance

1. **Viewing Logs**
   ```bash
   docker-compose logs -f
   ```

2. **Updating the Application**
   ```bash
   git pull
   docker-compose down
   docker-compose up -d --build
   ```

3. **Stopping the Application**
   ```bash
   docker-compose down
   ```

### Security Considerations
1. Use AWS Security Groups to restrict access
2. Keep your OpenAI API key secure
3. Regularly update your system and dependencies
4. Implement proper authentication
5. Use HTTPS in production

### Monitoring
1. Set up basic CloudWatch monitoring (free tier)
2. Monitor CPU and memory usage
3. Set up alarms for resource utilization
4. Monitor application logs 