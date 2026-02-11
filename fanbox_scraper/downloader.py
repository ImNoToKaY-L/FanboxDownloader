"""
Image downloader with ordered downloading and file management.
"""

import os
import logging
import time
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse
import requests
from PIL import Image
from io import BytesIO


class ImageDownloader:
    """
    Downloads images from URLs in order and manages file storage.
    """

    def __init__(self, session: requests.Session, download_dir: str = "downloads"):
        """
        Initialize the image downloader.

        Args:
            session: Requests session for downloading
            download_dir: Directory to save downloaded images
        """
        self.session = session
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def download_images(self, image_urls: List[str], prefix: str = "") -> List[str]:
        """
        Download images from URLs in order.

        Args:
            image_urls: List of image URLs to download
            prefix: Optional prefix for filenames

        Returns:
            List of paths to successfully downloaded files
        """
        downloaded_files = []

        for index, url in enumerate(image_urls, start=1):
            try:
                file_path = self.download_image(url, index, prefix)
                if file_path:
                    downloaded_files.append(file_path)
                    self.logger.info(f"Downloaded {index}/{len(image_urls)}: {file_path}")
                else:
                    self.logger.warning(f"Failed to download {index}/{len(image_urls)}: {url}")

                time.sleep(0.5)

            except Exception as e:
                self.logger.error(f"Error downloading image {url}: {e}")
                continue

        return downloaded_files

    def download_image(self, url: str, index: int, prefix: str = "") -> Optional[str]:
        """
        Download a single image.

        Args:
            url: Image URL
            index: Index number for ordering
            prefix: Optional filename prefix

        Returns:
            Path to downloaded file, or None if failed
        """
        try:
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type and not self._is_image_url(url):
                self.logger.warning(f"URL does not appear to be an image: {url}")
                return None

            extension = self._get_extension(url, content_type)
            filename = f"{prefix}{index:04d}{extension}"
            file_path = self.download_dir / filename

            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            if self._verify_image(file_path):
                return str(file_path)
            else:
                self.logger.warning(f"Downloaded file is not a valid image: {file_path}")
                file_path.unlink()
                return None

        except requests.RequestException as e:
            self.logger.error(f"Request error downloading {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error downloading {url}: {e}")
            return None

    def _is_image_url(self, url: str) -> bool:
        """
        Check if URL appears to be an image.

        Args:
            url: URL to check

        Returns:
            True if appears to be image URL
        """
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
        parsed = urlparse(url)
        path_lower = parsed.path.lower()
        return any(path_lower.endswith(ext) for ext in image_extensions)

    def _get_extension(self, url: str, content_type: str) -> str:
        """
        Determine file extension from URL or content type.

        Args:
            url: Image URL
            content_type: HTTP Content-Type header

        Returns:
            File extension including dot
        """
        parsed = urlparse(url)
        path = parsed.path.lower()

        extensions = {
            '.jpg': '.jpg',
            '.jpeg': '.jpg',
            '.png': '.png',
            '.gif': '.gif',
            '.webp': '.webp',
            '.bmp': '.bmp',
            '.svg': '.svg'
        }

        for ext in extensions:
            if path.endswith(ext):
                return extensions[ext]

        content_type_map = {
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'image/bmp': '.bmp',
            'image/svg+xml': '.svg'
        }

        for ct, ext in content_type_map.items():
            if ct in content_type:
                return ext

        return '.jpg'

    def _verify_image(self, file_path: Path) -> bool:
        """
        Verify that downloaded file is a valid image.

        Args:
            file_path: Path to file

        Returns:
            True if valid image
        """
        try:
            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception as e:
            self.logger.debug(f"Image verification failed for {file_path}: {e}")
            return False

    def get_download_stats(self) -> dict:
        """
        Get statistics about downloaded files.

        Returns:
            Dictionary with download statistics
        """
        files = list(self.download_dir.glob('*'))
        total_size = sum(f.stat().st_size for f in files if f.is_file())

        return {
            'total_files': len(files),
            'total_size_mb': total_size / (1024 * 1024),
            'download_dir': str(self.download_dir)
        }

    def clear_downloads(self):
        """
        Clear all downloaded files.
        """
        for file in self.download_dir.glob('*'):
            if file.is_file():
                file.unlink()
        self.logger.info("Cleared all downloads")
