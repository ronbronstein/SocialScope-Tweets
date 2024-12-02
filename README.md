# SocialScope-Tweets 🚀

A Matrix-themed Twitter scraper that lets you grab tweets, replies, or both from any public Twitter account. Clean UI, easy to use, gets the job done.

## What it Does 🎯

* Scrapes tweets and replies from Twitter accounts
* Matrix-style UI because why not
* Filter by date range
* Real-time progress tracking
* Saves everything to CSV
* Built-in rate limiting to keep things smooth

## Setup 🛠️

1. Clone it:
```bash
git clone git@github.com:yourusername/SocialScope-Tweets.git
cd SocialScope-Tweets
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

3. Get your API key from [socialdata.tools](https://socialdata.tools)

4. Create a `.env` file:
```bash
TWITTER_API_KEY=your_api_key_here
```

## Usage 💻

1. Run it:
```bash
python main.py
```

2. In the GUI:
   * Type in a username
   * Pick your dates
   * Choose what to grab (tweets/replies/both)
   * Hit START

3. Find your data in the `output` folder as CSV files

## What You Get 📊

CSV files with:
* Tweet text and creation date
* Likes, retweets, quotes, views
* Reply and retweet info
* Hashtags and mentions
* URLs shared

## Notes 📝

* Works with public accounts only
* Respects rate limits
* Date filtering available