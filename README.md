# FanboxDownloader

A Python web scraper specifically designed for downloading content from **Pixiv Fanbox** (https://www.fanbox.cc) with authentication, page navigation, and ordered image downloading.

## Features

- **Pixiv Authentication**: Login with your Pixiv credentials or use existing session ID
- **Fanbox Content Parsing**: Extract images and content from Fanbox posts
- **Creator Support**: Download all posts from a specific creator
- **Ordered Image Downloading**: Download images in the order they appear on the page
- **Multi-Source Image Detection**: Detect images from img tags, srcset, lazy-loading, and background images
- **Session Management**: Maintain authenticated sessions across requests
- **Flexible Authentication**: Use username/password or FANBOXSESSID cookie
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

### Method 1: Using Pixiv Credentials

```bash
python main.py \
  --url https://creator-name.fanbox.cc \
  --username your_pixiv_username \
  --password your_pixiv_password
```

### Method 2: Using Session ID (Recommended for Security)

1. Login to Fanbox in your browser
2. Open Developer Tools (F12)
3. Go to Application → Cookies → https://www.fanbox.cc
4. Copy the value of `FANBOXSESSID` cookie

```bash
python main.py \
  --url https://creator-name.fanbox.cc \
  --session-id YOUR_FANBOXSESSID_HERE
```

### Create Example Configuration

```bash
python main.py --create-example-config
```

This creates a `.env.example` file. Copy it to `.env` and update with your settings:

```bash
cp .env.example .env
nano .env  # Edit with your credentials
python main.py --config .env
```

## Configuration

### Using .env File

Create a `.env` file with your settings:

```ini
# Authentication Method 1: Pixiv Credentials
USERNAME=your_pixiv_username
PASSWORD=your_pixiv_password

# Authentication Method 2: Session ID (Alternative)
# Get this from browser cookies after logging in
FANBOXSESSID=your_session_id_here

# Fanbox URLs
# Examples:
#   https://creator-name.fanbox.cc
#   https://www.fanbox.cc/@creator-name
#   https://creator-name.fanbox.cc/posts/123456
START_URL=https://www.fanbox.cc/@creator-name

# Optional: Creator ID to download all posts
CREATOR_ID=creator-name

# Download settings
DOWNLOAD_DIR=downloads
FOLLOW_LINKS=true
MAX_DEPTH=3
DELAY_BETWEEN_REQUESTS=1.0
```

Then run:
```bash
python main.py --config .env
```

### Command-Line Arguments

```
--url URL                  Fanbox URL to scrape (creator page or specific post)
--config CONFIG            Path to configuration file (.env)
--username USERNAME        Pixiv username for login
--password PASSWORD        Pixiv password for login
--session-id SESSION_ID    FANBOXSESSID cookie value (alternative to username/password)
--download-dir DIR         Directory to save images (default: downloads)
--follow-links             Follow navigation links to additional pages
--max-depth DEPTH          Maximum depth for following links (default: 3)
--show-config              Display current configuration and exit
--create-example-config    Create an example .env.example file
```

### How to Get FANBOXSESSID Cookie

1. **Login to Fanbox** in your browser (Chrome, Firefox, etc.)
2. **Open Developer Tools**:
   - Chrome/Edge: Press `F12` or `Ctrl+Shift+I`
   - Firefox: Press `F12` or `Ctrl+Shift+I`
   - Safari: Enable Developer menu, then press `Cmd+Option+I`
3. **Navigate to Cookies**:
   - Chrome: Application → Cookies → https://www.fanbox.cc
   - Firefox: Storage → Cookies → https://www.fanbox.cc
4. **Find FANBOXSESSID**: Look for the cookie named `FANBOXSESSID`
5. **Copy the Value**: Copy the entire value (it will be a long string)

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

1. **Authentication**:
   - Logs in to Pixiv using provided credentials
   - Obtains FANBOXSESSID cookie for Fanbox access
   - Alternatively, uses provided session ID
2. **Page Loading**: Fetches Fanbox URLs using the authenticated session
3. **Content Parsing**: Extracts images, posts, and navigation links from Fanbox pages
4. **Image Downloading**: Downloads all images in order with sequential numbering
5. **Link Following**: If enabled, follows links to additional posts/pages
6. **Ordered Output**: Images are saved as `0001.jpg`, `0002.png`, etc.

## Image Detection

The scraper detects images from multiple sources:

- Standard `<img>` tags with `src` attribute
- Lazy-loaded images with `data-src` or `data-lazy-src`
- Responsive images using `<picture>` and `srcset`
- Background images from CSS `background-image` properties

## Examples

### Example 1: Download from a Creator

```bash
python main.py \
  --url https://creator-name.fanbox.cc \
  --username your_pixiv_user \
  --password your_pixiv_pass \
  --download-dir creator_downloads
```

### Example 2: Download Specific Post

```bash
python main.py \
  --url https://creator-name.fanbox.cc/posts/123456 \
  --username your_pixiv_user \
  --password your_pixiv_pass
```

### Example 3: Using Session ID (More Secure)

```bash
python main.py \
  --url https://www.fanbox.cc/@creator-name \
  --session-id YOUR_FANBOXSESSID_HERE \
  --follow-links \
  --max-depth 10
```

### Example 4: Download Multiple Creators

```bash
# Creator 1
python main.py --url https://creator1.fanbox.cc --session-id YOUR_SESSION --download-dir creator1

# Creator 2
python main.py --url https://creator2.fanbox.cc --session-id YOUR_SESSION --download-dir creator2
```

### Example 5: Using Configuration File

Create `.env`:
```ini
# Use session ID (recommended)
FANBOXSESSID=your_session_id_here

# Or use credentials
# USERNAME=your_pixiv_username
# PASSWORD=your_pixiv_password

START_URL=https://creator-name.fanbox.cc
DOWNLOAD_DIR=fanbox_downloads
FOLLOW_LINKS=true
MAX_DEPTH=5
DELAY_BETWEEN_REQUESTS=1.0
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

## Important Notes

- **Authentication Required**: Most Fanbox content requires authentication
- **Rate Limiting**: Please be respectful of Fanbox servers. Default delay is 1 second between requests
- **Session Expiry**: Session IDs expire after some time. You'll need to get a fresh one
- **Private Content**: You can only download content from creators you support/subscribe to

## Legal Notice

This tool is for **personal use and educational purposes only**. Always respect:
- **Pixiv/Fanbox Terms of Service**: Only download content you have legitimate access to
- **Copyright**: Downloaded content belongs to the creators
- **Privacy**: Don't share downloaded content without permission
- **Rate Limiting**: Don't overwhelm servers with requests
- **Creator Rights**: Support creators by subscribing to their Fanbox

**Use responsibly and ethically.** This tool is meant to help you organize content you've already paid for or have access to, not to pirate or redistribute creator content.

## License

MIT License - See [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on the GitHub repository.
