# SocialScope-Tweets 🚀

A powerful tool for fetching, analyzing, and exporting Twitter/X data with tagging and multiple output formats.

## Features 🎯

* **Flexible Data Collection**: Fetch tweets, replies, or both from any public Twitter account
* **Smart Content Analysis**: Automated topic extraction, sentiment analysis, and writing style detection
* **Multiple Output Formats**: Export data to simple CSV, detailed CSV, and structured XML
* **Date Filtering**: Specify custom date ranges for data collection
* **Command-line Tools**: Simple scripts for account analysis and comprehensive tweet scraping
* **Organization**: Timestamped output folders with consistent file naming

## What Data You Get 📊

SocialScope-Tweets collects and processes comprehensive tweet data including:

* Tweet text and creation timestamps
* Engagement metrics (likes, retweets, replies)
* Content categorization (is_reply, is_retweet)
* Automatically extracted topics from tweet content
* Sentiment analysis (positive, negative, neutral)
* Writing style detection (question, exclamatory, emphatic, etc.)

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
# Create the .env file
echo "SOCIALDATA_API_KEY=your_api_key_here" > .env
```

## Usage 💻

### Quick Account Analysis

To get a quick overview of a Twitter account:

```bash
python scripts/count_tweets.py elonmusk
```

This will display basic account information including:
- Username and name
- Account creation date
- Location and bio
- Tweet statistics (count, followers, following)

### Comprehensive Tweet Analysis

For full tweet analysis with CSV and XML output:

```bash
python scripts/tweet_analyzer.py elonmusk --type both --max 200 --start-date 2023-01-01 --end-date 2023-12-31
```

Options:
- `username`: Twitter username without @
- `--type`: Type of tweets to fetch (`tweets`, `replies`, or `both`)
- `--max`: Maximum number of tweets to fetch (default: 1000)
- `--start-date`: Start date in YYYY-MM-DD format
- `--end-date`: End date in YYYY-MM-DD format
- `--output-dir`: Directory for output files (default: output)
- `--verbose`: Enable verbose logging

This will:
1. Fetch account information
2. Fetch tweets based on your filters
3. Process tweets and extract topics
4. Tag tweets with topics, sentiment, and writing style
5. Save results in multiple formats to the output directory:
   - `tweets_simple.csv`: Just tweet text and timestamp
   - `tweets_full.csv`: All tweet data with tags
   - `tweets.xml`: Complete XML representation with tags
   - `account_info.json`: Account information

The output will be saved in a folder named with the username and a timestamp, like: `output/elonmusk_20230215_123456/`

## Repository Structure 📁

```
SocialScope-Tweets/
├── scripts/                # Command-line scripts
│   ├── tweet_analyzer.py   # Main analysis script
│   └── count_tweets.py     # Account overview script
├── src/                    # Source code
│   └── core/               # Core modules
│       ├── socialdata_client.py  # API client
│       ├── tweet_fetcher.py      # Tweet fetching
│       ├── tweet_processor.py    # Processing and tagging
│       └── output_generator.py   # CSV/XML generation
├── output/                 # Output directory
├── logs/                   # Log files
├── .env                    # API key (you need to create this)
├── .gitignore              # Git ignore file
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

## XML Output Format 📄

The XML output is structured for easy analysis:

```xml
<TwitterData>
  <Metadata>
    <ExportDate>2023-09-15T12:34:56</ExportDate>
  </Metadata>
  <Account>
    <!-- Account information -->
  </Account>
  <TagReference>
    <!-- All topics and styles found in the dataset -->
    <Topics>
      <Topic>ai</Topic>
      <Topic>space</Topic>
      <!-- ... -->
    </Topics>
    <Styles>
      <Style>question</Style>
      <Style>exclamatory</Style>
      <!-- ... -->
    </Styles>
  </TagReference>
  <Tweets>
    <Tweet>
      <ID>123456789</ID>
      <CreatedAt>2023-09-14T10:30:00</CreatedAt>
      <Text>This is a tweet about AI!</Text>
      <!-- More tweet data -->
      <Tags>
        <Topics>
          <Topic>ai</Topic>
        </Topics>
        <Sentiment>positive</Sentiment>
        <Styles>
          <Style>exclamatory</Style>
        </Styles>
      </Tags>
    </Tweet>
    <!-- More tweets -->
  </Tweets>
</TwitterData>
```

## Limitations ⚠️

* Works with public Twitter accounts only
* Requires an API key from socialdata.tools
* Rate limits apply based on your API tier
* Large requests may take significant time to complete

## License 📝

MIT License - See LICENSE file for details