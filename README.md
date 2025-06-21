# Web Research Agent

This project is a web application that combines FastAPI backend with a Next.js frontend, using Redis for caching and data storage.

*Complete docs can be found in docs.md .*

*This is the minimal setup for running the project locally. For deployment or Docker-based execution, switch to the backend-chat or frontend-chat branch respectively.*

## Prerequisites

- Python 3.8 or higher
- Node.js (v16 or higher) and npm
- Docker and Docker Compose
- Git

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd web-research-agent
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

### 6. Frontend Setup (Required before running launch.py)

Before running the application, ensure the frontend is properly set up:

```bash
# Navigate to frontend directory
cd frontend/masonry-frontend-next

# Install dependencies (use --force if you encounter dependency conflicts)
npm install --force

# Build the frontend
npm run build

# Return to root directory
cd ../..
```

### 7. Running the Application

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
- `routers/`: FastAPI route handlers (app.py)
- `config/`: Configuration files for LLM Client and Redis
- `scripts/`: Utility scripts [analyzer, newsAggregator, webScraper, web(reserach)]
- `test/`: Test files for different functions (utilised in development env)
- `main.py`: Main FastAPI application entry point
- `launch.py`: Application launcher script

## Development Workflow

1. **Frontend Development**:
   - Make changes in the `frontend/masonry-frontend-next` directory
   - Run `npm run dev` for development with hot reloading
   - Use `npm run build` to create production build

2. **Backend Development**:
   - Make changes in the `routers` directory
   - The FastAPI server will automatically reload on changes
   - Use `uvicorn routers.app:app --reload` for development

3. **Testing Changes**:
   - Frontend: `npm run test` in the frontend directory
   - Backend: `pytest` in the root directory

## Additional Notes

- The Redis instance runs on port 6379 by default
- Make sure all required API keys are properly configured in the `.env` file
- The application uses async operations for better performance
- Redis is used for caching and temporary data storage
- Frontend development server runs on port 3000
- Backend API server runs on port 8000

## Troubleshooting

If you encounter any issues:

1. **Redis Issues**:
   ```bash
   # Check if Redis is running
   docker ps | grep redis
   
   # Restart Redis if needed
   docker restart redis-cache
   ```

2. **Environment Setup**:
   ```bash
   # Verify environment variables
   cat .env
   
   # Check if virtual environment is activated
   which python  # Should point to .venv directory
   ```

3. **Dependencies**:
   ```bash
   # Check Python dependencies
   pip list
   
   # Check Node.js dependencies
   cd frontend/masonry-frontend-next
   npm list
   
   # Clear npm cache if needed
   npm cache clean --force
   ```

4. **Common Issues**:
   - If frontend fails to start: Try `npm install --force` and `npm run build`
   - If backend fails to start: Check if port 8000 is available
   - If Redis connection fails: Ensure Redis container is running
   - If API calls fail: Verify all API keys in `.env` are correct

5. **Logs**:
   - Check the application logs for detailed error messages
   - Frontend logs are available in the browser console
   - Backend logs are shown in the terminal running the server 
