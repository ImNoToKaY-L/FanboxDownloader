"""
Authentication handler for Pixiv Fanbox login functionality.
"""

import requests
import logging
import json
import time
from typing import Dict, Optional
from bs4 import BeautifulSoup
from .config import Config


class AuthHandler:
    """
    Handles authentication and session management for Pixiv Fanbox.
    """

    PIXIV_LOGIN_URL = "https://accounts.pixiv.net/api/login"
    PIXIV_AUTH_URL = "https://accounts.pixiv.net/login"
    FANBOX_URL = "https://www.fanbox.cc"

    def __init__(self, session: requests.Session, config: Config):
        """
        Initialize authentication handler.

        Args:
            session: Requests session object
            config: Configuration object
        """
        self.session = session
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.is_authenticated = False

        # Set headers required for Fanbox
        self.session.headers.update({
            'Origin': 'https://www.fanbox.cc',
            'Referer': 'https://www.fanbox.cc/',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
        })

    def login(self, username: str, password: str) -> bool:
        """
        Perform login with Pixiv credentials for Fanbox access.

        Args:
            username: Pixiv username or email
            password: Pixiv password

        Returns:
            True if login successful, False otherwise
        """
        if not username or not password:
            self.logger.warning("No credentials provided, skipping authentication")
            return False

        try:
            self.logger.info("Initiating Pixiv Fanbox login...")

            # Step 1: Get login page to extract post_key
            response = self.session.get(self.PIXIV_AUTH_URL, timeout=30)
            response.raise_for_status()

            post_key = self._extract_post_key(response.text)
            if not post_key:
                self.logger.warning("Could not extract post_key, attempting login without it")

            # Step 2: Perform login
            login_data = {
                'pixiv_id': username,
                'password': password,
                'captcha': '',
                'g_recaptcha_response': '',
                'post_key': post_key or '',
                'source': 'accounts',
                'ref': '',
                'return_to': 'https://www.fanbox.cc'
            }

            self.logger.debug("Submitting login credentials...")
            response = self.session.post(
                self.PIXIV_LOGIN_URL,
                data=login_data,
                timeout=30,
                allow_redirects=True
            )

            # Check if login was successful
            if response.status_code == 200:
                try:
                    result = response.json()
                    if result.get('error'):
                        self.logger.error(f"Login failed: {result.get('message', 'Unknown error')}")
                        return False
                except json.JSONDecodeError:
                    pass

            # Step 3: Verify we have the necessary cookies
            time.sleep(1)
            self.is_authenticated = self._verify_fanbox_access()

            if self.is_authenticated:
                self.logger.info("Successfully authenticated with Pixiv Fanbox")
            else:
                self.logger.error("Authentication verification failed")

            return self.is_authenticated

        except requests.RequestException as e:
            self.logger.error(f"Login request failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during login: {e}")
            return False

    def _extract_post_key(self, html: str) -> Optional[str]:
        """
        Extract post_key from Pixiv login page.

        Args:
            html: HTML content

        Returns:
            post_key if found, None otherwise
        """
        try:
            soup = BeautifulSoup(html, 'lxml')

            # Look for post_key in input field
            post_key_input = soup.find('input', {'name': 'post_key'})
            if post_key_input and post_key_input.get('value'):
                return post_key_input['value']

            # Look for post_key in global config
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'pixiv.context.token' in script.string:
                    # Extract token from JavaScript
                    import re
                    match = re.search(r'pixiv\.context\.token\s*=\s*["\']([^"\']+)["\']', script.string)
                    if match:
                        return match.group(1)

        except Exception as e:
            self.logger.debug(f"Error extracting post_key: {e}")

        return None

    def _verify_fanbox_access(self) -> bool:
        """
        Verify if we have access to Fanbox after login.

        Returns:
            True if authenticated and have Fanbox access
        """
        try:
            # Check for FANBOXSESSID cookie
            cookies = self.session.cookies.get_dict()
            if 'FANBOXSESSID' in cookies:
                self.logger.debug("FANBOXSESSID cookie found")
                return True

            # Try accessing Fanbox to see if we're logged in
            response = self.session.get(self.FANBOX_URL, timeout=30)

            if response.status_code == 200:
                # Check if we're redirected to login page
                if 'login' not in response.url.lower():
                    self.logger.debug("Successfully accessed Fanbox without redirect")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error verifying Fanbox access: {e}")
            return False

    def login_with_session_id(self, session_id: str) -> bool:
        """
        Login using an existing FANBOXSESSID cookie.

        Args:
            session_id: FANBOXSESSID cookie value

        Returns:
            True if session is valid
        """
        self.logger.info("Attempting login with session ID...")

        # Set the FANBOXSESSID cookie
        self.session.cookies.set('FANBOXSESSID', session_id, domain='.fanbox.cc')

        # Verify the session works
        self.is_authenticated = self._verify_fanbox_access()

        if self.is_authenticated:
            self.logger.info("Successfully authenticated with session ID")
        else:
            self.logger.error("Invalid session ID")

        return self.is_authenticated

    def get_authenticated_session(self) -> requests.Session:
        """
        Get the authenticated session.

        Returns:
            Authenticated requests session
        """
        return self.session

    def is_logged_in(self) -> bool:
        """
        Check if currently logged in.

        Returns:
            True if authenticated
        """
        return self.is_authenticated
