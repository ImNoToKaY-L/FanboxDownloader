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

        self.login_url = os.getenv('LOGIN_URL', '')
        self.username = os.getenv('USERNAME', '')
        self.password = os.getenv('PASSWORD', '')
        self.start_url = os.getenv('START_URL', '')
        self.download_dir = os.getenv('DOWNLOAD_DIR', 'downloads')
        self.follow_links = os.getenv('FOLLOW_LINKS', 'true').lower() == 'true'
        self.max_depth = int(os.getenv('MAX_DEPTH', '3'))
        self.delay_between_requests = float(os.getenv('DELAY_BETWEEN_REQUESTS', '0.5'))

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
        print(f"  Login URL: {self.login_url or 'Not set'}")
        print(f"  Username: {'***' if self.username else 'Not set'}")
        print(f"  Password: {'***' if self.password else 'Not set'}")
        print(f"  Start URL: {self.start_url or 'Not set'}")
        print(f"  Download Directory: {self.download_dir}")
        print(f"  Follow Links: {self.follow_links}")
        print(f"  Max Depth: {self.max_depth}")
        print(f"  Delay Between Requests: {self.delay_between_requests}s")
        print()

    @classmethod
    def create_example_env(cls, path: str = ".env.example"):
        """
        Create an example .env file.

        Args:
            path: Path to create example file
        """
        example_content = """# FanboxDownloader Configuration

# Login credentials (optional if no authentication required)
LOGIN_URL=https://example.com/login
USERNAME=your_username
PASSWORD=your_password

# Starting URL for scraping
START_URL=https://example.com/page/to/scrape

# Download settings
DOWNLOAD_DIR=downloads
FOLLOW_LINKS=true
MAX_DEPTH=3
DELAY_BETWEEN_REQUESTS=0.5
"""

        with open(path, 'w') as f:
            f.write(example_content)

        print(f"Created example configuration file: {path}")
        print("Copy this to .env and update with your settings")
