"""
FanboxDownloader - A web scraper for downloading content with authentication.
"""

__version__ = "1.0.0"
__author__ = "ImNoToKaY"

from .scraper import FanboxScraper
from .config import Config

__all__ = ['FanboxScraper', 'Config']
