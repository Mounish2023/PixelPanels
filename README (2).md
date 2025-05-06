# PixelPanels - AI Comic Creator

PixelPanels is an AI-powered comic book creator that generates children's comics from text prompts using OpenAI's GPT-4 and DALL-E models.

## Project Structure

```
pixelpanels/
├── app/
│   ├── __init__.py
│   ├── config.py          # Application configuration
│   ├── main.py            # FastAPI application
│   ├── models/            # Pydantic models
│   │   └── comic_models.py
│   ├── routes/            # API routes
│   │   ├── __init__.py
│   │   └── comic_routes.py
│   ├── services/          # Business logic
│   │   ├── openai_service.py
│   │   └── image_service.py
│   └── utils/             # Utility functions
│       └── file_utils.py
├── static/                # Static files (CSS, JS, images)
│   ├── css/
│   ├── js/
│   └── images/
├── tests/                 # Test files
├── .env                   # Environment variables
└── requirements.txt       # Python dependencies
```

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd pixelpanels
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with your OpenAI API key:
   ```
   OPENAI_API_KEY=your-api-key-here
   DEBUG=True
   ```

5. Run the application:
   ```bash
   cd pixelpanels
   uvicorn app.main:app --reload
   ```

6. Access the API documentation at `http://localhost:8000/docs`

## API Endpoints

- `POST /api/v1/comics/generate` - Start comic generation
- `GET /api/v1/comics/status/{job_id}` - Check status of comic generation
- `GET /api/v1/comics/files/{project_id}/{file_type}/{filename}` - Access generated files

## Frontend

The frontend is a single-page application that interacts with the backend API. To use it:

1. Make sure the backend is running
2. Open `frontend/index.html` in a web browser
3. Enter a story prompt and click "Create Comic"

## Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Use a production ASGI server like Gunicorn with Uvicorn workers:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app
   ```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT
