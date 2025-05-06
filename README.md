# AI Comic Creator App

An interactive web application that helps children create personalized comic stories with AI assistance.

## Overview

The AI Comic Creator App allows children to easily create custom comic stories by providing a simple prompt. The application leverages AI technologies to:

1. Generate a short story based on the child's prompt
2. Break down the story into sequential panels
3. Create pixel art for each panel
4. Assemble a complete comic book with images and text
5. Generate an audio narration of the story
6. Package everything together for a rich interactive experience

## Features

- **Intuitive User Interface**: Designed specifically for children with a colorful, friendly interface
- **AI Story Generation**: Creates unique stories based on simple prompts
- **Pixel Art Generation**: Converts story panels into kid-friendly pixel art illustrations
- **Voice Narration**: Adds audio narration to bring the story to life
- **Easy Sharing**: Download or share the finished comics
- **Real-time Progress Tracking**: Shows children what's happening as their comic is created

## Technical Architecture

### Backend (FastAPI)

The backend is built with FastAPI and handles all AI interactions:

- **Story Generation**: Uses OpenAI GPT-4 to create original stories
- **Story Breakdown**: Segments stories into logical panels
- **Image Generation**: Uses OpenAI DALL-E to create pixel art for each panel
- **Comic Assembly**: Combines images and text into a well-formatted comic
- **Audio Generation**: Creates voice narration using OpenAI's text-to-speech

### Frontend (HTML/CSS/JavaScript)

The frontend provides an engaging user experience:

- **Responsive Design**: Works on various devices and screen sizes
- **Progress Tracking**: Real-time updates on the comic creation process
- **Tab Navigation**: Easy switching between views (full comic, individual panels, story text)
- **Download Options**: Save comics and audio files locally
- **Sharing Capabilities**: Share creations with friends and family

## Setup and Installation

### Prerequisites

- Python 3.8+
- Node.js (optional, for development)
- OpenAI API key

### Backend Setup

1. Clone the repository
2. Install Python dependencies:
   ```
   pip install fastapi uvicorn openai python-multipart pillow
   ```
3. Set your OpenAI API key:
   ```
   export OPENAI_API_KEY="your-api-key"
   ```
4. Run the FastAPI server:
   ```
   uvicorn main:app --reload
   ```

### Frontend Setup

The frontend is static HTML/CSS/JS and can be served from any web server. For development:

1. Open the HTML file directly in a browser
2. Update the `API_BASE_URL` in the JavaScript to point to your backend server

## Usage

1. Open the application in a web browser
2. Enter a story prompt (e.g., "A friendly dragon who learns to fly")
3. Select a story style and optionally add character names
4. Click "Create My Comic!"
5. Wait for the AI to generate your comic (typically 1-3 minutes)
6. Explore the finished comic with narration
7. Download or share your creation

## API Documentation

When running, the FastAPI backend provides automatic API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Main Endpoints

- **POST /generate-comic**: Start comic generation process
- **GET /status/{project_id}**: Check comic generation status
- **GET /files/{project_id}/{file_type}/{filename}**: Access generated files
- **GET /health**: Health check endpoint

## Future Enhancements

- Multiple comic styles (superhero, manga, etc.)
- Character customization options
- Background music selection
- Extended story options (longer stories, series)
- Collaborative creation with friends
- Custom drawing tools to modify AI-generated art

## License

This project is licensed under the MIT License.

## Acknowledgments

- OpenAI for GPT-4, DALL-E, and TTS technologies
- FastAPI for the backend framework
- The open-source community for various tools and libraries
