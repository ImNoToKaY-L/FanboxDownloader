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
        description='FanboxDownloader - Pixiv Fanbox scraper with login and ordered image downloading',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download from a specific creator
  python main.py --url https://creator-name.fanbox.cc --username user --password pass

  # Download a specific post
  python main.py --url https://creator-name.fanbox.cc/posts/123456 --username user --password pass

  # Use session ID instead of credentials
  python main.py --url https://www.fanbox.cc/@creator --session-id YOUR_FANBOXSESSID

  # Use configuration file
  python main.py --config .env --follow-links --max-depth 5

  # Create example configuration
  python main.py --create-example-config
        """
    )

    parser.add_argument(
        '--url',
        help='Starting URL to scrape (e.g., https://creator.fanbox.cc or https://www.fanbox.cc/@creator)'
    )

    parser.add_argument(
        '--config',
        help='Path to configuration file (.env)',
        default=None
    )

    parser.add_argument(
        '--username',
        help='Pixiv username for login'
    )

    parser.add_argument(
        '--password',
        help='Pixiv password for login'
    )

    parser.add_argument(
        '--session-id',
        help='FANBOXSESSID cookie value (alternative to username/password)'
    )

    parser.add_argument(
        '--login-url',
        help='Login page URL (default: https://accounts.pixiv.net/login)'
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

    # Uncensor options
    parser.add_argument(
        '--enable-uncensor',
        action='store_true',
        help='Enable automatic uncensoring of downloaded images (requires: pip install -r requirements-uncensor.txt)'
    )

    parser.add_argument(
        '--uncensor-device',
        choices=['cpu', 'cuda', 'mps'],
        default='cpu',
        help='Device for uncensoring (cpu, cuda for NVIDIA GPU, mps for Apple Silicon)'
    )

    parser.add_argument(
        '--uncensor-model',
        choices=['lama'],
        default='lama',
        help='Model to use for uncensoring (default: lama)'
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
    if hasattr(args, 'session_id') and args.session_id:
        config.session_id = args.session_id
    if args.login_url:
        config.login_url = args.login_url
    if args.download_dir:
        config.download_dir = args.download_dir
    if args.follow_links:
        config.follow_links = True
    if args.max_depth:
        config.max_depth = args.max_depth
    if args.enable_uncensor:
        config.enable_uncensor = True
    if args.uncensor_device:
        config.uncensor_device = args.uncensor_device
    if args.uncensor_model:
        config.uncensor_model = args.uncensor_model

    if args.show_config:
        config.display()
        return 0

    if not config.validate():
        parser.print_help()
        return 1

    print("=" * 60)
    print("FanboxDownloader - Pixiv Fanbox Scraper")
    print("=" * 60)

    config.display()

    scraper = FanboxScraper(config)

    try:
        # Attempt authentication
        if config.session_id or (config.username and config.password):
            print("Logging in...")
            if not scraper.login(
                username=config.username,
                password=config.password,
                session_id=config.session_id
            ):
                print("Login failed. Exiting...")
                return 1
            else:
                print("Login successful!")
        else:
            print("Warning: No authentication provided. Some content may not be accessible.")
            print("Provide --username and --password, or --session-id to authenticate.\n")

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
