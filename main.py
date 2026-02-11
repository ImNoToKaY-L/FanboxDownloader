#!/usr/bin/env python3
"""
FanboxDownloader - Main entry point
A web scraper for downloading content with authentication and ordered image downloading.
"""

import sys
import argparse
from pathlib import Path
from fanbox_scraper import FanboxScraper, Config


def main():
    """Main entry point for the FanboxDownloader."""
    parser = argparse.ArgumentParser(
        description='FanboxDownloader - Web scraper with login and ordered image downloading',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --url https://example.com/page
  python main.py --config .env --follow-links --max-depth 5
  python main.py --url https://example.com --username user --password pass
  python main.py --create-example-config
        """
    )

    parser.add_argument(
        '--url',
        help='Starting URL to scrape'
    )

    parser.add_argument(
        '--config',
        help='Path to configuration file (.env)',
        default=None
    )

    parser.add_argument(
        '--username',
        help='Username for login'
    )

    parser.add_argument(
        '--password',
        help='Password for login'
    )

    parser.add_argument(
        '--login-url',
        help='Login page URL'
    )

    parser.add_argument(
        '--download-dir',
        help='Directory to save downloaded images',
        default='downloads'
    )

    parser.add_argument(
        '--follow-links',
        action='store_true',
        help='Follow navigation links to additional pages'
    )

    parser.add_argument(
        '--max-depth',
        type=int,
        default=3,
        help='Maximum depth for following links (default: 3)'
    )

    parser.add_argument(
        '--create-example-config',
        action='store_true',
        help='Create an example .env.example configuration file'
    )

    parser.add_argument(
        '--show-config',
        action='store_true',
        help='Display current configuration and exit'
    )

    args = parser.parse_args()

    if args.create_example_config:
        Config.create_example_env()
        return 0

    config = Config(args.config)

    if args.url:
        config.start_url = args.url
    if args.username:
        config.username = args.username
    if args.password:
        config.password = args.password
    if args.login_url:
        config.login_url = args.login_url
    if args.download_dir:
        config.download_dir = args.download_dir
    if args.follow_links:
        config.follow_links = True
    if args.max_depth:
        config.max_depth = args.max_depth

    if args.show_config:
        config.display()
        return 0

    if not config.validate():
        parser.print_help()
        return 1

    print("=" * 60)
    print("FanboxDownloader - Web Scraper")
    print("=" * 60)

    config.display()

    scraper = FanboxScraper(config)

    try:
        if config.username and config.password:
            print("Logging in...")
            if not scraper.login(config.username, config.password):
                print("Login failed. Continuing without authentication...")
            else:
                print("Login successful!")

        print(f"\nStarting scraping from: {config.start_url}")
        print("-" * 60)

        results = scraper.scrape_and_download(
            config.start_url,
            follow_links=config.follow_links,
            max_depth=config.max_depth
        )

        print("\n" + "=" * 60)
        print("Scraping Complete!")
        print("=" * 60)
        print(f"Pages visited: {results['pages_visited']}")
        print(f"Images downloaded: {results['images_downloaded']}")
        print(f"Download location: {config.download_dir}")
        print("=" * 60)

        stats = scraper.downloader.get_download_stats()
        print(f"\nTotal files: {stats['total_files']}")
        print(f"Total size: {stats['total_size_mb']:.2f} MB")

        return 0

    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user.")
        return 130

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        scraper.close()


if __name__ == '__main__':
    sys.exit(main())
