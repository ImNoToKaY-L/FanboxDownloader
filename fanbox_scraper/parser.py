"""
Page content parser for extracting images and links.
"""

import logging
import re
from typing import Dict, List
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests


class PageParser:
    """
    Parses HTML content to extract images and navigation links.
    """

    def __init__(self, session: requests.Session):
        """
        Initialize the parser.

        Args:
            session: Requests session for fetching pages
        """
        self.session = session
        self.logger = logging.getLogger(__name__)

    def parse(self, html: str, base_url: str) -> Dict:
        """
        Parse HTML content and extract relevant data.

        Args:
            html: HTML content to parse
            base_url: Base URL for resolving relative links

        Returns:
            Dictionary containing extracted images and navigation links
        """
        soup = BeautifulSoup(html, 'lxml')

        images = self._extract_images(soup, base_url)
        next_pages = self._extract_navigation_links(soup, base_url)

        return {
            'images': images,
            'next_pages': next_pages,
            'title': self._extract_title(soup),
            'content': self._extract_content(soup)
        }

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract all image URLs from the page in order.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative URLs

        Returns:
            List of absolute image URLs
        """
        image_urls = []
        seen_urls = set()

        img_tags = soup.find_all('img')

        for img in img_tags:
            src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')

            if not src:
                continue

            absolute_url = urljoin(base_url, src)

            if absolute_url in seen_urls:
                continue

            if self._is_valid_image_url(absolute_url):
                image_urls.append(absolute_url)
                seen_urls.add(absolute_url)

        picture_tags = soup.find_all('picture')
        for picture in picture_tags:
            source_tags = picture.find_all('source')
            for source in source_tags:
                srcset = source.get('srcset')
                if srcset:
                    urls = self._parse_srcset(srcset, base_url)
                    for url in urls:
                        if url not in seen_urls and self._is_valid_image_url(url):
                            image_urls.append(url)
                            seen_urls.add(url)

        divs_with_bg = soup.find_all(['div', 'section', 'article'], style=re.compile(r'background-image'))
        for div in divs_with_bg:
            style = div.get('style', '')
            urls = re.findall(r'url\(["\']?([^"\']+)["\']?\)', style)
            for url in urls:
                absolute_url = urljoin(base_url, url)
                if absolute_url not in seen_urls and self._is_valid_image_url(absolute_url):
                    image_urls.append(absolute_url)
                    seen_urls.add(absolute_url)

        self.logger.info(f"Extracted {len(image_urls)} unique images")
        return image_urls

    def _parse_srcset(self, srcset: str, base_url: str) -> List[str]:
        """
        Parse srcset attribute to extract image URLs.

        Args:
            srcset: srcset attribute value
            base_url: Base URL for resolving relative URLs

        Returns:
            List of absolute image URLs
        """
        urls = []
        entries = srcset.split(',')

        for entry in entries:
            parts = entry.strip().split()
            if parts:
                url = parts[0]
                absolute_url = urljoin(base_url, url)
                urls.append(absolute_url)

        return urls

    def _is_valid_image_url(self, url: str) -> bool:
        """
        Check if URL is a valid image URL.

        Args:
            url: URL to check

        Returns:
            True if valid image URL
        """
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return False

            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']
            path_lower = parsed.path.lower()

            if any(path_lower.endswith(ext) for ext in image_extensions):
                return True

            if 'image' in parsed.path.lower():
                return True

            return False

        except Exception:
            return False

    def _extract_navigation_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract navigation links to related content pages.

        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative URLs

        Returns:
            List of absolute URLs
        """
        nav_links = []
        seen_urls = set()

        nav_keywords = ['next', 'continue', 'more', 'page', 'post', 'article']

        links = soup.find_all('a', href=True)

        for link in links:
            href = link.get('href')
            text = link.get_text().strip().lower()
            classes = ' '.join(link.get('class', [])).lower()

            if any(keyword in text or keyword in classes for keyword in nav_keywords):
                absolute_url = urljoin(base_url, href)

                if absolute_url not in seen_urls and self._is_same_domain(absolute_url, base_url):
                    nav_links.append(absolute_url)
                    seen_urls.add(absolute_url)

        self.logger.info(f"Found {len(nav_links)} navigation links")
        return nav_links

    def _is_same_domain(self, url1: str, url2: str) -> bool:
        """
        Check if two URLs are from the same domain.

        Args:
            url1: First URL
            url2: Second URL

        Returns:
            True if same domain
        """
        try:
            domain1 = urlparse(url1).netloc
            domain2 = urlparse(url2).netloc
            return domain1 == domain2
        except Exception:
            return False

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """
        Extract page title.

        Args:
            soup: BeautifulSoup object

        Returns:
            Page title
        """
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()

        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()

        return "Untitled"

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """
        Extract main content text from the page.

        Args:
            soup: BeautifulSoup object

        Returns:
            Main content text
        """
        main_content = soup.find(['article', 'main', 'div'], class_=['content', 'post', 'article'])

        if main_content:
            return main_content.get_text(strip=True)[:500]

        return soup.get_text(strip=True)[:500]
