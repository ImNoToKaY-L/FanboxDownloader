"""
Authentication handler for login functionality.
"""

import requests
import logging
from typing import Dict, Optional
from bs4 import BeautifulSoup
from .config import Config


class AuthHandler:
    """
    Handles authentication and session management.
    """

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

    def login(self, username: str, password: str) -> bool:
        """
        Perform login with username and password.

        Args:
            username: User's username or email
            password: User's password

        Returns:
            True if login successful, False otherwise
        """
        login_url = self.config.login_url

        if not login_url:
            self.logger.warning("No login URL configured, skipping authentication")
            return True

        try:
            response = self.session.get(login_url, timeout=30)
            response.raise_for_status()

            csrf_token = self._extract_csrf_token(response.text)

            login_data = {
                'username': username,
                'password': password,
            }

            if csrf_token:
                login_data['csrf_token'] = csrf_token

            response = self.session.post(
                login_url,
                data=login_data,
                timeout=30,
                allow_redirects=True
            )

            self.is_authenticated = self._verify_login(response)

            return self.is_authenticated

        except requests.RequestException as e:
            self.logger.error(f"Login request failed: {e}")
            return False

    def _extract_csrf_token(self, html: str) -> Optional[str]:
        """
        Extract CSRF token from HTML if present.

        Args:
            html: HTML content

        Returns:
            CSRF token if found, None otherwise
        """
        try:
            soup = BeautifulSoup(html, 'lxml')

            csrf_input = soup.find('input', {'name': 'csrf_token'})
            if csrf_input and csrf_input.get('value'):
                return csrf_input['value']

            csrf_meta = soup.find('meta', {'name': 'csrf-token'})
            if csrf_meta and csrf_meta.get('content'):
                return csrf_meta['content']

        except Exception as e:
            self.logger.debug(f"Error extracting CSRF token: {e}")

        return None

    def _verify_login(self, response: requests.Response) -> bool:
        """
        Verify if login was successful.

        Args:
            response: Response from login request

        Returns:
            True if login successful
        """
        if response.status_code != 200:
            return False

        soup = BeautifulSoup(response.text, 'lxml')

        error_indicators = soup.find_all(['div', 'span'], class_=['error', 'alert', 'warning'])
        if any('login' in elem.text.lower() or 'password' in elem.text.lower() for elem in error_indicators):
            return False

        success_indicators = [
            soup.find('div', class_=['dashboard', 'profile', 'account']),
            soup.find('a', text='Logout'),
            soup.find('a', text='Sign Out'),
        ]

        if any(success_indicators):
            return True

        if 'Set-Cookie' in response.headers:
            return True

        return True

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
