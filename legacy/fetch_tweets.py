import requests
import pandas as pd
import time
from datetime import datetime
import os
from typing import List, Dict
import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tweet_fetch.log'),
        logging.StreamHandler()
    ]
)

# Configuration
API_KEY = "1387|IEGGoVbn86qHo89TpoNi5SkrJETRofLIHdBVVlq8d68f6526"  # Replace with your API key
SEARCH_URL = "https://api.socialdata.tools/twitter/search"
RATE_LIMIT_PAUSE = 1  # Seconds to wait between requests
MAX_RETRIES = 3

# Updated date range
START_DATE = int(datetime(2024, 9, 1).timestamp())
END_DATE = int(datetime(2024, 12, 31).timestamp())

# List of search queries - removed quotes to catch more variations
SEARCH_QUERIES = [
    'MegaMind Quiz',
    'megaeth quiz',
    '@megaeth_labs quiz',
    'mega eth quiz',
    'mega mind quiz'
]

def fetch_tweets(query: str, retries: int = MAX_RETRIES) -> List[Dict]:
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Accept': 'application/json'
    }
    
    all_tweets = []
    cursor = None
    total_processed = 0
    retry_count = 0
    
    while True:
        try:
            # Construct query with date range
            date_query = f"{query} since_time:{START_DATE} until_time:{END_DATE}"
            
            params = {
                'query': date_query,
                'type': 'Latest'
            }
            
            if cursor:
                params['cursor'] = cursor
            
            logging.info(f"Fetching tweets for query: {query} (cursor: {cursor is not None})")
            
            # Add rate limiting pause
            time.sleep(RATE_LIMIT_PAUSE)
            
            response = requests.get(SEARCH_URL, headers=headers, params=params)
            
            # Handle HTTP errors
            response.raise_for_status()
            
            data = response.json()
            
            # Check if we got tweets
            if 'tweets' not in data or not data['tweets']:
                logging.info(f"No more tweets found for query: {query}")
                break
                
            tweets = data['tweets']
            all_tweets.extend(tweets)
            total_processed += len(tweets)
            logging.info(f"Query: {query} - Processed {len(tweets)} new tweets (Total: {total_processed})")
            
            # Check for next cursor
            cursor = data.get('next_cursor')
            if not cursor:
                logging.info(f"No more pages available for query: {query}")
                break
            
            retry_count = 0  # Reset retry count on successful request
                
        except requests.exceptions.RequestException as e:
            retry_count += 1
            if retry_count >= retries:
                logging.error(f"Max retries reached for query '{query}': {e}")
                break
            
            logging.warning(f"Error fetching tweets (attempt {retry_count}/{retries}): {e}")
            time.sleep(retry_count * 2)  # Exponential backoff
            continue
            
    logging.info(f"Total tweets fetched for query '{query}': {len(all_tweets)}")
    return all_tweets

def process_tweet(tweet: Dict) -> Dict:
    """Extract relevant fields from a tweet"""
    return {
        'tweet_id': tweet['id_str'],
        'created_at': tweet['tweet_created_at'],
        'text': tweet['full_text'],
        'author': tweet['user']['screen_name'],
        'retweets': tweet['retweet_count'],
        'likes': tweet['favorite_count'],
        'views': tweet['views_count'],
        'matched_query': tweet.get('matched_query', ''),
        'url': f"https://twitter.com/{tweet['user']['screen_name']}/status/{tweet['id_str']}"
    }

def main():
    all_processed_tweets = []
    seen_tweet_ids = set()
    
    try:
        # If there's an existing CSV, load its tweet IDs to prevent duplicates
        existing_files = [f for f in os.listdir('.') if f.startswith('mega_quiz_tweets_') and f.endswith('.csv')]
        if existing_files:
            latest_file = max(existing_files)
            logging.info(f"Found existing file: {latest_file}")
            existing_df = pd.read_csv(latest_file)
            seen_tweet_ids.update(existing_df['tweet_id'].astype(str))
            logging.info(f"Loaded {len(seen_tweet_ids)} existing tweet IDs")
    except Exception as e:
        logging.warning(f"Error loading existing tweets: {e}")
    
    for query in SEARCH_QUERIES:
        try:
            logging.info(f"\nStarting fetch for query: {query}")
            tweets = fetch_tweets(query)
            
            # Process tweets and add query information
            for tweet in tweets:
                tweet['matched_query'] = query
                
                if tweet['id_str'] not in seen_tweet_ids:
                    processed_tweet = process_tweet(tweet)
                    all_processed_tweets.append(processed_tweet)
                    seen_tweet_ids.add(tweet['id_str'])
                else:
                    logging.debug(f"Skipping duplicate tweet ID: {tweet['id_str']}")
            
            logging.info(f"Processed {len(tweets)} tweets for query: {query}")
            
        except Exception as e:
            logging.error(f"Error processing query '{query}': {e}")
            continue
    
    # Create final DataFrame and save to CSV
    if all_processed_tweets:
        df = pd.DataFrame(all_processed_tweets)
        
        # Sort by created_at date
        df['created_at'] = pd.to_datetime(df['created_at'])
        df = df.sort_values('created_at', ascending=False)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mega_quiz_tweets_{timestamp}.csv"
        
        df.to_csv(filename, index=False)
        logging.info(f"\nSaved {len(df)} unique tweets to {filename}")
        logging.info("Breakdown by query:")
        logging.info("\n" + str(df['matched_query'].value_counts()))
        
        # Save summary stats
        summary = {
            'total_tweets': len(df),
            'unique_authors': df['author'].nunique(),
            'date_range': f"{df['created_at'].min()} to {df['created_at'].max()}",
            'tweets_by_query': df['matched_query'].value_counts().to_dict()
        }
        
        with open(f"summary_{timestamp}.json", 'w') as f:
            json.dump(summary, f, indent=2)
        logging.info(f"Saved summary stats to summary_{timestamp}.json")
    else:
        logging.warning("No tweets found for any query")

if __name__ == "__main__":
    main()