"""API routes package."""
from fastapi import APIRouter

# Create a base router for all API routes
router = APIRouter()

# Import all route modules here
from . import comic_routes  # noqa
