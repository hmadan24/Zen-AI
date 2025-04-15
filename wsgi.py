from app import app
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Configure the application
app.config['ENV'] = 'production'
app.config['DEBUG'] = False

# Get the port from the environment variable or use default
port = int(os.environ.get('PORT', 3000))

# Log environment variables (excluding sensitive ones)
logger.info("Environment variables:")
for key, value in os.environ.items():
    if 'KEY' not in key.upper() and 'SECRET' not in key.upper():
        logger.info(f"{key}: {value}")

if __name__ == "__main__":
    try:
        logger.info("Starting Flask application...")
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"Error starting Flask application: {str(e)}")
        raise 