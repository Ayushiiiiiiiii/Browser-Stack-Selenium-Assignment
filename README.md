# El País Opinion Section Scraper

Web scraper for El País Opinion section with BrowserStack parallel testing.

## Features

- Scrapes first 5 articles from El País Opinion section
- Downloads article cover images
- Translates titles from Spanish to English
- Analyzes word frequency in translated headers
- Parallel testing on BrowserStack (5 browsers)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Local Testing
```bash
python elpais_scraper.py
```

### BrowserStack Testing
1. Add your BrowserStack credentials to `browserstack_test.py`
2. Run:
```bash
python browserstack_test.py
```

## Output

- **article_images/** - Downloaded article images
- **scraping_results.json** - Scraped article data

## Author

Technical Assignment for BrowserStack