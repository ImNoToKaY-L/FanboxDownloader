"""
Main scraper class that orchestrates the web scraping process.
"""

import requests
import logging
from pathlib import Path
from typing import Optional, List, Dict
from .auth import AuthHandler
from .parser import PageParser
from .downloader import ImageDownloader
from .config import Config


class FanboxScraper:
    """
    Main scraper class for handling web scraping with authentication.
    """

    def __init__(self, config: Config):
        """
        Initialize the scraper with configuration.

        Args:
            config: Configuration object containing scraper settings
        """
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        self.auth_handler = AuthHandler(self.session, config)
        self.parser = PageParser(self.session)
        self.downloader = ImageDownloader(self.session, config.download_dir)

        self.logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('fanbox_scraper.log'),
                logging.StreamHandler()
            ]
        )

    def login(self, username: str = None, password: str = None, session_id: str = None) -> bool:
        """
        Perform login with credentials or session ID.

        Args:
            username: Pixiv username or email (optional if session_id provided)
            password: Pixiv password (optional if session_id provided)
            session_id: FANBOXSESSID cookie value (alternative to username/password)

        Returns:
            True if login successful, False otherwise
        """
        # Try session ID first if provided
        if session_id:
            self.logger.info("Attempting login with session ID...")
            success = self.auth_handler.login_with_session_id(session_id)
            if success:
                self.logger.info("Login successful with session ID")
                return True
            else:
                self.logger.warning("Session ID login failed, trying username/password if available")

        # Try username/password
        if username and password:
            self.logger.info(f"Attempting login for user: {username}")
            success = self.auth_handler.login(username, password)

            if success:
                self.logger.info("Login successful")
            else:
                self.logger.error("Login failed")

            return success

        self.logger.warning("No valid authentication method provided")
        return False

    def scrape_page(self, url: str) -> Dict:
        """
        Scrape a single page and extract content.

        Args:
            url: URL of the page to scrape

        Returns:
            Dictionary containing page data and image URLs
        """
        self.logger.info(f"Scraping page: {url}")

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            page_data = self.parser.parse(response.text, url)
            self.logger.info(f"Found {len(page_data.get('images', []))} images")

            return page_data

        except requests.RequestException as e:
            self.logger.error(f"Error scraping page {url}: {e}")
            return {'images': [], 'next_pages': []}

    def download_images(self, image_urls: List[str], prefix: str = "") -> List[str]:
        """
        Download images in order.

        Args:
            image_urls: List of image URLs to download
            prefix: Optional prefix for downloaded files

        Returns:
            List of paths to downloaded files
        """
        self.logger.info(f"Downloading {len(image_urls)} images")
        downloaded_files = self.downloader.download_images(image_urls, prefix)
        self.logger.info(f"Successfully downloaded {len(downloaded_files)} images")

        return downloaded_files

    def scrape_and_download(self, start_url: str, follow_links: bool = True, max_depth: int = 3) -> Dict:
        """
        Complete scraping and downloading workflow.

        Args:
            start_url: Starting URL for scraping
            follow_links: Whether to follow links to additional pages
            max_depth: Maximum depth for following links

        Returns:
            Dictionary with download statistics
        """
        visited = set()
        to_visit = [(start_url, 0)]
        all_downloaded = []

        while to_visit:
            url, depth = to_visit.pop(0)

            if url in visited or depth > max_depth:
                continue

            visited.add(url)

            page_data = self.scrape_page(url)

            if page_data.get('images'):
                prefix = f"page_{len(visited)}_"
                downloaded = self.download_images(page_data['images'], prefix)
                all_downloaded.extend(downloaded)

            if follow_links and depth < max_depth:
                for next_url in page_data.get('next_pages', []):
                    if next_url not in visited:
                        to_visit.append((next_url, depth + 1))

        return {
            'pages_visited': len(visited),
            'images_downloaded': len(all_downloaded),
            'downloaded_files': all_downloaded
        }

    def close(self):
        """Close the session and cleanup resources."""
        self.session.close()
        self.logger.info("Scraper session closed")
