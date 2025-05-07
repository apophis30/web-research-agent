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