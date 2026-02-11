# FanboxDownloader

A Python web scraper for downloading content with authentication, page navigation, and ordered image downloading.

## Features

- **Mock Login**: Authenticate with username/password before scraping
- **Page Content Reading**: Parse and extract content from web pages
- **Smart Navigation**: Follow links to additional pages automatically
- **Ordered Image Downloading**: Download images in the order they appear on the page
- **Image Recognition**: Detect images from multiple sources (img tags, srcset, background images)
- **Session Management**: Maintain authenticated sessions across requests
- **Configurable**: Use command-line arguments or .env configuration file

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ImNoToKaY-L/FanboxDownloader.git
cd FanboxDownloader
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Quick Start

### Create Example Configuration

```bash
python main.py --create-example-config
```

This creates a `.env.example` file. Copy it to `.env` and update with your settings:

```bash
cp .env.example .env
```

### Basic Usage

Scrape a single page without authentication:
```bash
python main.py --url https://example.com/page
```

Scrape with authentication:
```bash
python main.py --url https://example.com/page --username your_user --password your_pass --login-url https://example.com/login
```

Follow links to additional pages:
```bash
python main.py --url https://example.com/page --follow-links --max-depth 5
```

## Configuration

### Using .env File

Create a `.env` file with your settings:

```ini
# Login credentials (optional)
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
```

Then run:
```bash
python main.py --config .env
```

### Command-Line Arguments

```
--url URL                  Starting URL to scrape
--config CONFIG            Path to configuration file (.env)
--username USERNAME        Username for login
--password PASSWORD        Password for login
--login-url LOGIN_URL      Login page URL
--download-dir DIR         Directory to save images (default: downloads)
--follow-links             Follow navigation links to additional pages
--max-depth DEPTH          Maximum depth for following links (default: 3)
--show-config              Display current configuration and exit
--create-example-config    Create an example .env.example file
```

## Project Structure

```
FanboxDownloader/
├── fanbox_scraper/          # Main package
│   ├── __init__.py          # Package initialization
│   ├── scraper.py           # Main scraper class
│   ├── auth.py              # Authentication handler
│   ├── parser.py            # Page content parser
│   ├── downloader.py        # Image downloader
│   └── config.py            # Configuration manager
├── main.py                  # CLI entry point
├── requirements.txt         # Python dependencies
├── .gitignore              # Git ignore rules
├── LICENSE                  # MIT License
└── README.md               # This file
```

## How It Works

1. **Authentication**: If credentials are provided, the scraper logs in and maintains the session
2. **Page Loading**: Fetches the starting URL using the authenticated session
3. **Content Parsing**: Extracts images and navigation links from the page
4. **Image Downloading**: Downloads all images in order with sequential numbering
5. **Link Following**: If enabled, follows navigation links to scrape additional pages
6. **Ordered Output**: Images are saved as `0001.jpg`, `0002.png`, etc.

## Image Detection

The scraper detects images from multiple sources:

- Standard `<img>` tags with `src` attribute
- Lazy-loaded images with `data-src` or `data-lazy-src`
- Responsive images using `<picture>` and `srcset`
- Background images from CSS `background-image` properties

## Examples

### Example 1: Simple Scraping

```bash
python main.py --url https://example.com/gallery --download-dir my_images
```

### Example 2: With Authentication

```bash
python main.py \
  --url https://example.com/members/gallery \
  --login-url https://example.com/login \
  --username myuser \
  --password mypass \
  --download-dir downloads
```

### Example 3: Follow Links

```bash
python main.py \
  --url https://example.com/series/page1 \
  --follow-links \
  --max-depth 10 \
  --download-dir series_images
```

### Example 4: Using Configuration File

Create `.env`:
```ini
START_URL=https://example.com/gallery
LOGIN_URL=https://example.com/login
USERNAME=myuser
PASSWORD=mypass
DOWNLOAD_DIR=my_downloads
FOLLOW_LINKS=true
MAX_DEPTH=5
```

Run:
```bash
python main.py --config .env
```

## Output

Downloaded images are saved with sequential numbering:
```
downloads/
├── 0001.jpg
├── 0002.png
├── 0003.jpg
├── page_2_0001.jpg
├── page_2_0002.jpg
└── ...
```

## Logging

The scraper creates a `fanbox_scraper.log` file with detailed information about:
- Login attempts and results
- Pages scraped
- Images found and downloaded
- Errors and warnings

## Requirements

- Python 3.7+
- requests
- beautifulsoup4
- lxml
- Pillow
- python-dotenv

## Legal Notice

This tool is for educational purposes and authorized use only. Always respect:
- Website terms of service
- Robots.txt directives
- Rate limiting and server resources
- Copyright and intellectual property rights

Use responsibly and only on websites where you have permission to scrape content.

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on the GitHub repository.
