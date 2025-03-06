# SocialScope-Tweets 🚀

A Matrix-themed Twitter scraper that lets you grab tweets, replies, or both from any public Twitter account. The tool features a clean UI and is designed to be easy to use while providing comprehensive data collection capabilities.

![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)

## Features 🎯

* **Targeted Scraping**: Collect tweets, replies, or both from any public Twitter account
* **Date Filtering**: Specify custom date ranges for data collection
* **Rate Limiting**: Built-in controls to prevent API throttling
* **Progress Tracking**: Real-time feedback on the scraping process
* **CSV Export**: All data is saved in a structured CSV format
* **Matrix UI**: Enjoy a cyberpunk-inspired interface

## What Data You Get 📊

SocialScope-Tweets collects comprehensive tweet data including:

* Tweet text and creation timestamps
* Engagement metrics (likes, retweets, quotes, views, replies)
* Content categorization (is_reply, is_retweet)
* Media attachment counts
* Hashtags used in tweets
* Account mentions
* URLs shared in tweets

## Prerequisites 📋

* Python 3.7+
* API key from [socialdata.tools](https://socialdata.tools)
* Internet connection

## Installation 🛠️

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SocialScope-Tweets.git
cd SocialScope-Tweets
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API key:
```bash
# Create from example
cp .env.example .env
# Edit the file to add your API key
```

## Usage 💻

1. Start the application:
```bash
python main.py
```

2. In the GUI:
   * Enter the target username (without @)
   * Set your desired date range
   * Choose what to collect (tweets/replies/both)
   * Set the maximum number of tweets to collect
   * Click "START SCRAPING"

3. Monitor progress in the status section
4. When complete, find your data in the `output` folder as CSV files
5. Use the "OPEN FILE" button to directly access the most recently saved file

## Folder Structure 📁

```
SocialScope-Tweets/
├── main.py            # GUI application
├── scraper.py         # Twitter scraping logic
├── config.json.example # Example configuration
├── .env.example       # Example environment variables
├── requirements.txt   # Python dependencies
├── LICENSE            # MIT License
├── CONTRIBUTING.md    # Contribution guidelines
├── README.md          # This file
├── logs/              # Application logs (created at runtime)
└── output/            # Scraped data output (created at runtime)
```

## Limitations ⚠️

* Works with public Twitter accounts only
* Requires an API key from socialdata.tools
* Rate limits apply based on your API tier
* Large requests may take significant time to complete