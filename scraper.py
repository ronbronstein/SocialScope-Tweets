import requests
import csv
import logging
import time
from datetime import datetime, timedelta
import os
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from pathlib import Path
import json
from dotenv import load_dotenv

@dataclass
class ScraperConfig:
    """Configuration for Twitter scraper"""
    username: str
    max_tweets: int = 1000
    scrape_type: str = 'both'  # 'tweets', 'replies', or 'both'
    save_dir: str = 'output'
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    rate_limit_calls: int = 30
    rate_limit_period: int = 60
    request_timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5

class RateLimiter:
    """Rate limiter implementation"""
    def __init__(self, max_calls: int, period: int):
        self.max_calls = max_calls
        self.period = period
        self.calls = []

    def wait_if_needed(self):
        """Wait if rate limit is reached"""
        now = time.time()
        self.calls = [call for call in self.calls if call > now - self.period]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = self.calls[0] - (now - self.period)
            if sleep_time > 0:
                logging.info(f"Rate limit reached. Waiting {sleep_time:.2f} seconds...")
                time.sleep(sleep_time)
        
        self.calls.append(now)

class TwitterScraper:
    """Enhanced Twitter scraper implementation"""
    
    def __init__(self, config: ScraperConfig):
        """Initialize scraper with configuration"""
        self.config = config
        self.api_key = self.get_api_key()
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        }
        self.rate_limiter = RateLimiter(
            self.config.rate_limit_calls,
            self.config.rate_limit_period
        )
        self.setup_directories()
        self.user_id = None
        self.seen_tweets = set()
        
    def setup_directories(self):
        """Create necessary directories"""
        for directory in ['logs', 'output', 'cache']:
            Path(directory).mkdir(exist_ok=True)

    def get_api_key(self) -> str:
        """Get API key from .env file"""
        try:
            load_dotenv()
            api_key = os.getenv('TWITTER_API_KEY')
            if not api_key:
                raise ValueError("TWITTER_API_KEY not found in .env file")
            return api_key
        except Exception as e:
            logging.critical(f"Failed to load API key: {e}")
            raise

    def make_request(self, url: str, params: Dict = None) -> Dict:
        """Make API request with retry logic and rate limiting"""
        for attempt in range(self.config.retry_attempts):
            try:
                self.rate_limiter.wait_if_needed()
                
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=self.config.request_timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    wait_time = int(response.headers.get('Retry-After', self.config.retry_delay))
                    logging.warning(f"Rate limit hit. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    response.raise_for_status()
                    
            except requests.Timeout:
                logging.warning(f"Request timeout (attempt {attempt + 1}/{self.config.retry_attempts})")
            except requests.RequestException as e:
                logging.error(f"Request failed: {e} (attempt {attempt + 1}/{self.config.retry_attempts})")
            
            if attempt < self.config.retry_attempts - 1:
                time.sleep(self.config.retry_delay)
        
        raise Exception("Max retry attempts reached")

    def verify_account(self) -> Dict:
        """Verify Twitter account and get details"""
        try:
            url = f"https://api.socialdata.tools/twitter/user/{self.config.username}"
            data = self.make_request(url)
            
            self.user_id = data.get('id_str')
            
            return {
                'success': True,
                'user_id': data.get('id_str'),
                'name': data.get('name'),
                'total_tweets': data.get('statuses_count'),
                'followers': data.get('followers_count'),
                'protected': data.get('protected', False),
                'verified': data.get('verified', False),
                'created_at': data.get('created_at')
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def fetch_tweets(self, progress_callback: Callable[[float, str, bool], None] = None) -> List[Dict]:
        """Fetch tweets based on configuration"""
        all_tweets = []
        cursor = None
        consecutive_errors = 0
        
        try:
            # Construct query based on type and date range
            query = f"from:{self.config.username}"
            if self.config.scrape_type == 'tweets':
                query += " -filter:replies"
            elif self.config.scrape_type == 'replies':
                query += " filter:replies"

            # Add date range to query if specified
            if self.config.start_date:
                start_timestamp = int(self.config.start_date.timestamp())
                query += f" since_time:{start_timestamp}"
            if self.config.end_date:
                end_timestamp = int(self.config.end_date.timestamp())
                query += f" until_time:{end_timestamp}"

            logging.info(f"Starting tweet collection with query: {query}")
            
            while len(all_tweets) < self.config.max_tweets:
                try:
                    url = "https://api.socialdata.tools/twitter/search"
                    params = {
                        'query': query,
                        'type': 'Latest'
                    }
                    
                    if cursor:
                        params['cursor'] = cursor

                    data = self.make_request(url, params)
                    tweets = data.get('tweets', [])
                    
                    if not tweets:
                        logging.info("No more tweets available")
                        if progress_callback:
                            progress_callback(100, "Collection complete", True)
                        break

                    # Process new tweets
                    new_tweets_count = 0
                    for tweet in tweets:
                        tweet_id = tweet.get('id_str')
                        if tweet_id and tweet_id not in self.seen_tweets:
                            self.seen_tweets.add(tweet_id)
                            all_tweets.append(tweet)
                            new_tweets_count += 1
                            
                            if len(all_tweets) >= self.config.max_tweets:
                                logging.info(f"Reached target of {self.config.max_tweets} tweets")
                                if progress_callback:
                                    progress_callback(100, "Collection complete", True)
                                break

                    # Update progress
                    if progress_callback:
                        progress = min(100, (len(all_tweets) / self.config.max_tweets) * 100)
                        status = f"Collected {len(all_tweets):,} tweets"
                        is_complete = not cursor or len(all_tweets) >= self.config.max_tweets
                        progress_callback(progress, status, is_complete)

                    # Log progress
                    logging.info(f"Collected {new_tweets_count} new tweets (Total: {len(all_tweets)})")

                    # Get next cursor
                    cursor = data.get('next_cursor')
                    if not cursor:
                        logging.info("No more pages available")
                        if progress_callback:
                            progress_callback(100, "Collection complete", True)
                        break

                    # Reset error counter on successful request
                    consecutive_errors = 0
                    
                    # Small delay between requests
                    time.sleep(0.5)

                except Exception as e:
                    consecutive_errors += 1
                    logging.error(f"Error during tweet collection: {str(e)}")
                    
                    if consecutive_errors >= self.config.retry_attempts:
                        logging.error("Max consecutive errors reached")
                        break
                    
                    time.sleep(self.config.retry_delay)

            logging.info(f"Tweet collection completed. Total tweets: {len(all_tweets)}")
            return all_tweets

        except Exception as e:
            logging.error(f"Fatal error during tweet collection: {str(e)}")
            return all_tweets

    def save_tweets(self, tweets: List[Dict]) -> str:
        """
        Save tweets to CSV file
        
        Args:
            tweets: List of tweets to save
            
        Returns:
            Path to saved file or empty string on failure
        """
        if not tweets:
            return ""

        try:
            # Create filename with details
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            tweet_type = {
                'tweets': 'tweets_only',
                'replies': 'replies_only',
                'both': 'tweets_and_replies'
            }[self.config.scrape_type]
            
            filename = Path(self.config.save_dir) / f'{self.config.username}_{tweet_type}_{timestamp}_{len(tweets)}_tweets.csv'

            logging.info(f"Saving tweets to {filename}")

            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'tweet_id', 'created_at', 'text', 'likes', 'retweets',
                    'quotes', 'views', 'replies', 'is_reply', 'is_retweet',
                    'media_count', 'hashtags', 'mentions', 'urls'
                ])
                
                writer.writeheader()
                for tweet in tweets:
                    writer.writerow({
                        'tweet_id': tweet.get('id_str'),
                        'created_at': tweet.get('tweet_created_at'),
                        'text': tweet.get('full_text'),
                        'likes': tweet.get('favorite_count'),
                        'retweets': tweet.get('retweet_count'),
                        'quotes': tweet.get('quote_count'),
                        'views': tweet.get('views_count'),
                        'replies': tweet.get('reply_count'),
                        'is_reply': tweet.get('in_reply_to_status_id_str') is not None,
                        'is_retweet': tweet.get('retweeted_status') is not None,
                        'media_count': len(tweet.get('media', [])),
                        'hashtags': ','.join(h['text'] for h in tweet.get('entities', {}).get('hashtags', [])),
                        'mentions': ','.join(m['screen_name'] for m in tweet.get('entities', {}).get('user_mentions', [])),
                        'urls': ','.join(u['expanded_url'] for u in tweet.get('entities', {}).get('urls', []))
                    })

            logging.info(f"Successfully saved {len(tweets)} tweets to {filename}")
            return str(filename)
            
        except Exception as e:
            logging.error(f"Error saving tweets: {str(e)}")
            return ""

    def calculate_rate_limit_delay(self) -> float:
        """Calculate delay needed for rate limiting"""
        now = time.time()
        self.rate_limiter.calls = [t for t in self.rate_limiter.calls if t > now - self.rate_limiter.period]
        
        if len(self.rate_limiter.calls) >= self.rate_limiter.max_calls:
            return max(0, self.rate_limiter.calls[0] - (now - self.rate_limiter.period))
        return 0

if __name__ == "__main__":
    # Example usage
    try:
        config = ScraperConfig(
            username="example_user",
            max_tweets=100,
            scrape_type='both'
        )
        
        scraper = TwitterScraper(config)
        account_info = scraper.verify_account()
        
        if account_info['success']:
            print(f"Account verified: {account_info['name']}")
            tweets = scraper.fetch_tweets()
            
            if tweets:
                filename = scraper.save_tweets(tweets)
                print(f"Saved tweets to {filename}")
            else:
                print("No tweets collected")
        else:
            print(f"Failed to verify account: {account_info.get('error')}")
            
    except Exception as e:
        print(f"Error: {e}")