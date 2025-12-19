# Google OAuth Configuration
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OAuth credentials - now loaded from .env file
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

# Flask configuration (optional - Flask can generate if not provided)
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Validate required environment variables
if not GOOGLE_CLIENT_ID:
    raise ValueError("GOOGLE_CLIENT_ID environment variable is required")
if not GOOGLE_CLIENT_SECRET:
    raise ValueError("GOOGLE_CLIENT_SECRET environment variable is required")

# Set environment variables for use in other modules
os.environ['GOOGLE_CLIENT_ID'] = GOOGLE_CLIENT_ID
os.environ['GOOGLE_CLIENT_SECRET'] = GOOGLE_CLIENT_SECRET
os.environ['SECRET_KEY'] = SECRET_KEY
