"""Logging configuration for NeuraBuddy."""

import logging
import sys
from pathlib import Path

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/neurabuddy.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("neurabuddy")

