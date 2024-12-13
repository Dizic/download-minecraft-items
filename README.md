# Minecraft Items Image Downloader

Script for automatically downloading Minecraft item images from the Minecraft Wiki.

## Description

This script automates downloading item images from Minecraft Wiki by:
1. Fetching a complete list of Minecraft items via the Wiki API
2. Finding associated images for each item
3. Downloading and saving images to a local directory

## Features

- Multi-threaded downloads for better performance
- Configurable delay between requests to avoid rate limiting
- Comprehensive error handling and logging
- Sanitizes filenames for cross-platform compatibility
- Progress tracking and download statistics
- Generates JSON file with item metadata
- Optional file downloading (can collect metadata only)

## Requirements

- Python 3.6+
- Required packages:
  - requests
  - concurrent.futures (built-in)
  - logging (built-in)

## Configuration

The script uses the following configurable settings:
- `SAVE_DIR`: Directory to save downloaded images (default: 'scripts/minecraft_items')
- `ITEMS_PER_REQUEST`: Number of items per API request (default: 50)
- `MAX_WORKERS`: Maximum number of concurrent download threads (default: 10)
- `DELAY_BETWEEN_REQUESTS`: Delay between API requests in seconds (default: 1)

## Logging

The script logs all operations to:
- Console output
- 'minecraft_items_download.log' file

## Usage

### Basic usage (metadata only, no downloads):
```bash
python download_minecraft_items.py
```

### Download files and collect metadata:
```bash
python download_minecraft_items.py --download
```
