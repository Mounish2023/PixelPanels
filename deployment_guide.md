# Deployment Guide: AI Comic Creator App

This guide provides instructions for deploying the AI Comic Creator App in both development and production environments.

## Development Environment

### Backend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-comic-creator.git
   cd ai-comic-creator
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install fastapi uvicorn openai python-multipart pillow pydantic asyncio httpx
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=your_openai_api_key
   ENVIRONMENT=development
   ```

5. **Run the development server**
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   The backend API will be available at: http://localhost:8000

### Frontend Setup

For development, you can simply open the `index.html` file in your browser, or use a simple HTTP server:

**Using Python's built-in HTTP server:**
```bash
cd frontend
python -m http.server
```
Access the frontend at: http://localhost:8000

**Using Node.js (if you prefer):**
```bash
npm install -g http-server
cd frontend
http-server
```
Access the frontend at: http://localhost:8080

### Development Configuration

In the frontend JavaScript, make sure the API endpoint is set to your local development server:
```javascript
const API_BASE_URL = 'http://localhost:8000';
```

## Production Deployment

### Backend Deployment

#### Option 1: Docker Deployment

1. **Create a Dockerfile**
   ```dockerfile
   FROM python:3.9-slim

   WORKDIR /app

   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. **Create a requirements.txt file**
   ```
   fastapi==0.103.1
   uvicorn==0.23.2
   openai==0.28.0
   python-multipart==0.0.6
   pillow==10.0.0
   pydantic==2.3.0
   python-dotenv==1.0.0
   httpx==0.24.1
   ```

3. **Build and run the Docker container**
   ```bash
   docker build -t ai-comic-creator .
   docker run -d -p 8000:8000 -e OPENAI_API_KEY=your_openai_api_key --name ai-comic-creator ai-comic-creator
   ```

#### Option 2: Cloud Deployment (Example with Heroku)

1. **Install the Heroku CLI and login**
   ```bash
   heroku login
   ```

2. **Create a new Heroku app**
   ```bash
   heroku create ai-comic-creator
   ```

3. **Add a Procfile**
   ```
   web: uvicorn main:app --host=0.0.0.0 --port=$PORT
   ```

4. **Set up environment variables**
   ```bash
   heroku config:set OPENAI_API_KEY=your_openai_api_key
   heroku config:set ENVIRONMENT=production
   ```

5. **Deploy the app**
   ```bash
   git push heroku main
   ```

### Frontend Deployment

The frontend is static HTML/CSS/JS and can be deployed to any static site hosting service:

#### Option 1: Netlify

1. **Sign up for Netlify**
2. **Drag and drop the frontend folder** to Netlify's upload area or connect your Git repository
3. **Update the API_BASE_URL** in `script.js` to point to your production backend

#### Option 2: GitHub Pages

1. **Create a GitHub repository** and push your code
2. **Enable GitHub Pages** in the repository settings
3. **Update the API_BASE_URL** in `script.js` to point to your production backend

## Configuration for Production

Update the `API_BASE_URL` in the frontend JavaScript to point to your production backend:
```javascript
const API_BASE_URL = 'https://your-production-backend.com';
```

## Security Considerations

For production deployment, implement these security best practices:

1. **API Key Security**
   - Never expose your OpenAI API key in frontend code
   - Set rate limits to prevent abuse

2. **CORS Configuration**
   In production, restrict CORS to your frontend domain:
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-frontend-domain.com"],
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

3. **Content Monitoring**
   - Implement filters to ensure age-appropriate content
   - Add monitoring for content policy violations

4. **User Authentication**
   - Consider adding user accounts for persistent storage and content tracking
   - Implement rate limiting per user to prevent abuse

## Scaling Considerations

1. **Database Integration**
   Replace the in-memory storage with a proper database:
   - PostgreSQL for relational data
   - MongoDB for document storage
   - AWS S3 or similar for generated media files

2. **Background Processing**
   For better scalability, use a proper task queue:
   ```python
   # Example with Celery
   from celery import Celery
   
   celery_app = Celery(
       "comic_creator",
       broker="redis://localhost:6379/0",
       backend="redis://localhost:6379/0"
   )
   
   @celery_app.task
   def process_comic_generation(project_id, story_prompt):
       # Task processing code here
   ```

3. **Load Balancing**
   - Deploy multiple instances behind a load balancer
   - Use CDN for static content distribution

## Monitoring and Logging

1. **Application Logging**
   ```python
   import logging
   
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
       handlers=[
           logging.FileHandler("app.log"),
           logging.StreamHandler()
       ]
   )
   ```

2. **Monitoring Services**
   - Set up Prometheus and Grafana for metrics
   - Configure alerts for errors and performance issues

## Update and Maintenance

1. **Backup Strategy**
   - Regularly backup user data and generated content
   - Document backup and restore procedures

2. **Update Process**
   - Create a staging environment for testing updates
   - Implement CI/CD pipeline for automated testing and deployment

3. **Documentation**
   - Maintain API documentation with OpenAPI/Swagger
   - Document all configuration options and deployment procedures

## Support and Troubleshooting

Common issues and solutions:

1. **OpenAI API errors**
   - Check API key validity
   - Verify API rate limits and quotas
   - Ensure prompt content adheres to OpenAI content policy

2. **File storage issues**
   - Verify file permissions on storage directories
   - Monitor disk space usage
   - Implement proper file cleanup for temporary files

3. **Performance issues**
   - Monitor API response times
   - Check server resource utilization
   - Optimize image processing and generation steps
