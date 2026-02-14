"""
Configuration handler for scraper settings.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """
    Configuration manager for FanboxScraper.
    """

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_file: Optional path to .env configuration file
        """
        if config_file and Path(config_file).exists():
            load_dotenv(config_file)
        else:
            load_dotenv()

        # Pixiv/Fanbox authentication
        self.login_url = os.getenv('LOGIN_URL', 'https://accounts.pixiv.net/login')
        self.username = os.getenv('USERNAME', '')
        self.password = os.getenv('PASSWORD', '')
        self.session_id = os.getenv('FANBOXSESSID', '')  # Optional: Use existing session

        # Fanbox URLs
        self.start_url = os.getenv('START_URL', '')
        self.creator_id = os.getenv('CREATOR_ID', '')  # Optional: Specific creator to download

        # Download settings
        self.download_dir = os.getenv('DOWNLOAD_DIR', 'downloads')
        self.follow_links = os.getenv('FOLLOW_LINKS', 'true').lower() == 'true'
        self.max_depth = int(os.getenv('MAX_DEPTH', '3'))
        self.delay_between_requests = float(os.getenv('DELAY_BETWEEN_REQUESTS', '0.5'))

        # Uncensor settings
        self.enable_uncensor = os.getenv('ENABLE_UNCENSOR', 'false').lower() == 'true'
        self.uncensor_model = os.getenv('UNCENSOR_MODEL', 'lama')
        self.uncensor_device = os.getenv('UNCENSOR_DEVICE', 'cpu')  # cpu, cuda, mps
        self.uncensor_auto_detect = os.getenv('UNCENSOR_AUTO_DETECT', 'true').lower() == 'true'
        self.uncensor_output_dir = os.getenv('UNCENSOR_OUTPUT_DIR', 'uncensored')
        self.uncensor_sensitivity = float(os.getenv('UNCENSOR_SENSITIVITY', '0.5'))
        self.uncensor_no_downscale = os.getenv('UNCENSOR_NO_DOWNSCALE', 'false').lower() == 'true'
        # If no_downscale is enabled, use a very large max_resolution
        if self.uncensor_no_downscale:
            self.uncensor_max_resolution = 999999
        else:
            self.uncensor_max_resolution = int(os.getenv('UNCENSOR_MAX_RESOLUTION', '2048'))

    def validate(self) -> bool:
        """
        Validate that required configuration is present.

        Returns:
            True if configuration is valid
        """
        if not self.start_url:
            print("Error: START_URL is required")
            return False

        return True

    def display(self):
        """
        Display current configuration (without sensitive data).
        """
        print("\nCurrent Configuration:")
        print(f"  Login URL: {self.login_url}")
        print(f"  Username: {'***' if self.username else 'Not set'}")
        print(f"  Password: {'***' if self.password else 'Not set'}")
        print(f"  Session ID: {'***' if self.session_id else 'Not set'}")
        print(f"  Creator ID: {self.creator_id or 'Not set'}")
        print(f"  Start URL: {self.start_url or 'Not set'}")
        print(f"  Download Directory: {self.download_dir}")
        print(f"  Follow Links: {self.follow_links}")
        print(f"  Max Depth: {self.max_depth}")
        print(f"  Delay Between Requests: {self.delay_between_requests}s")
        if self.enable_uncensor:
            print(f"  Uncensor: Enabled ({self.uncensor_model} on {self.uncensor_device})")
            print(f"  Uncensor Sensitivity: {self.uncensor_sensitivity}")
            print(f"  Uncensor Output: {self.uncensor_output_dir}")
        else:
            print(f"  Uncensor: Disabled")
        print()

    @classmethod
    def create_example_env(cls, path: str = ".env.example"):
        """
        Create an example .env file.

        Args:
            path: Path to create example file
        """
        example_content = """# FanboxDownloader Configuration for Pixiv Fanbox

# Authentication Method 1: Username and Password
# Your Pixiv account credentials
USERNAME=your_pixiv_username
PASSWORD=your_pixiv_password

# Authentication Method 2: Session ID (Alternative to username/password)
# You can extract FANBOXSESSID from your browser cookies after logging in
# FANBOXSESSID=your_session_id_here

# Fanbox Creator and Post URLs
# Example: https://creator-name.fanbox.cc
# Or: https://www.fanbox.cc/@creator-name
# Or specific post: https://creator-name.fanbox.cc/posts/123456
START_URL=https://www.fanbox.cc/@creator-name

# Optional: Specify a creator ID to download all their posts
CREATOR_ID=creator-name

# Download settings
DOWNLOAD_DIR=downloads
FOLLOW_LINKS=true
MAX_DEPTH=3
DELAY_BETWEEN_REQUESTS=1.0

# Image Uncensoring (requires: pip install -r requirements-uncensor.txt)
# Enable automatic uncensoring of downloaded images
ENABLE_UNCENSOR=false
UNCENSOR_MODEL=lama
UNCENSOR_DEVICE=cpu  # cpu, cuda (NVIDIA GPU), or mps (Apple Silicon)
UNCENSOR_AUTO_DETECT=true
UNCENSOR_OUTPUT_DIR=uncensored
# Detection sensitivity: 0.0-1.0 (default: 0.5)
# Use 0.7-0.9 for small/subtle mosaic patterns
# Higher values = more sensitive but may increase false positives
UNCENSOR_SENSITIVITY=0.5
# Maximum resolution for processing (default: 2048)
# Larger images will be downscaled to prevent memory errors
# Use 1024 for low memory, 4096 for high-end GPUs
UNCENSOR_MAX_RESOLUTION=2048
# Disable automatic downscaling (process at full resolution)
# WARNING: Requires 16GB+ RAM for large images. Set to 'true' only if needed.
UNCENSOR_NO_DOWNSCALE=false

# Advanced: Login URL (usually don't need to change this)
LOGIN_URL=https://accounts.pixiv.net/login
"""

        with open(path, 'w') as f:
            f.write(example_content)

        print(f"Created example configuration file: {path}")
        print("Copy this to .env and update with your settings")
