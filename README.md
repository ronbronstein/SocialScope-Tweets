# SocialScope-Tweets

A Python application with a Matrix-themed GUI for scraping and analyzing Twitter data. This tool offers a user-friendly interface to collect tweets, replies, and user information from specified Twitter accounts.

## Features

- 🎨 Matrix-themed graphical user interface
- 📊 Real-time progress tracking and status updates
- 📅 Date range filtering for targeted data collection
- 🔄 Multiple scraping modes (tweets only, replies only, or both)
- 💾 Automatic CSV export with comprehensive tweet data
- 📝 Detailed logging system with save/export capabilities
- ⚡ Rate limiting protection
- 🔐 Secure API key management

## Prerequisites

- Python 3.x
- Twitter API Key from [socialdata.tools](https://socialdata.tools)
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/SocialScope-Tweets.git
cd SocialScope-Tweets
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your API key:
   - Create a `.env` file in the project root directory
   - Add your socialdata.tools API key:
     ```
     TWITTER_API_KEY=your_api_key_here
     ```

## Configuration

The application uses several configuration files:

- `config.json`: Stores user preferences and last session data
- `.env`: Stores your API key
- `target_account.txt`: Contains target Twitter usernames

## Usage

1. Start the application:
```bash
python main.py
```

2. In the GUI:
   - Enter the target username
   - Select date range
   - Choose scraping type (tweets, replies, or both)
   - Set maximum number of tweets to collect
   - Click "START SCRAPING"

## Output

The tool generates the following outputs:

- CSV files in the `output/` directory with naming format:
  `{username}_{type}_{timestamp}_{tweet_count}_tweets.csv`
- Log files in the `logs/` directory
- Cache files in the `cache/` directory

## CSV Data Fields

- tweet_id
- created_at
- text
- likes
- retweets
- quotes
- views
- replies
- is_reply
- is_retweet
- media_count
- hashtags
- mentions
- urls

## Project Structure

```
SocialScope-Tweets/
├── main.py              # GUI implementation
├── scraper.py           # Core scraping functionality
├── config.json          # User preferences
├── .env                 # API key configuration
├── requirements.txt     # Python dependencies
├── cache/              # Cache directory
├── logs/               # Log files
└── output/             # CSV output files
```

## Important Notes

- You must obtain an API key from [socialdata.tools](https://socialdata.tools) before using this tool
- Respect Twitter's terms of service and rate limits
- Protected accounts cannot be scraped
- The tool includes built-in rate limiting and error handling

## Error Handling

The application includes comprehensive error handling for:
- Invalid API keys
- Network issues
- Rate limiting
- Protected accounts
- Invalid usernames
- Date validation

## License

[Add your chosen license here]

## Contributing

[Add contribution guidelines here]