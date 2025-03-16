# enhanced_scraper.py
import requests
import csv
import logging
import time
import json
import threading
import os
import queue
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Callable, Any, Set
from dataclasses import dataclass, field, asdict
from urllib.parse import urlparse
from dotenv import load_dotenv

# Custom Exception Classes
class ScraperException(Exception):
    """Base exception for scraper errors"""
    pass

class AuthenticationError(ScraperException):
    """Authentication error"""
    pass

class RateLimitError(ScraperException):
    """Rate limit exceeded"""
    pass

class ResourceNotFoundError(ScraperException):
    """Resource not found (404)"""
    pass

class NetworkError(ScraperException):
    """Network connectivity error"""
    pass

@dataclass
class ScraperConfig:
    """Enhanced configuration for Twitter scraper"""
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
    output_format: str = 'csv'  # 'csv', 'json', or 'sqlite'
    add_metadata: bool = True
    api_keys: List[str] = field(default_factory=list)
    api_key_rotation: str = 'sequential'
    proxy_url: Optional[str] = None
    user_agent: str = 'SocialScope-Tweets/1.0'
    export_formats: List[str] = field(default_factory=lambda: ['csv'])
    
    @classmethod
    def from_env(cls) -> 'ScraperConfig':
        """Load configuration from environment variables"""
        load_dotenv()
        
        # Get API keys (comma-separated)
        api_keys_str = os.getenv('TWITTER_API_KEYS', os.getenv('TWITTER_API_KEY', ''))
        api_keys = [k.strip() for k in api_keys_str.split(',') if k.strip()]
        
        # Parse dates
        start_date_str = os.getenv('TWITTER_START_DATE')
        end_date_str = os.getenv('TWITTER_END_DATE')
        
        start_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                logging.warning(f"Invalid start date format: {start_date_str}")
        
        end_date = None
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            except ValueError:
                logging.warning(f"Invalid end date format: {end_date_str}")
        
        # Create config
        return cls(
            username=os.getenv('TWITTER_USERNAME', ''),
            max_tweets=int(os.getenv('TWITTER_MAX_TWEETS', '1000')),
            scrape_type=os.getenv('TWITTER_SCRAPE_TYPE', 'both'),
            save_dir=os.getenv('TWITTER_SAVE_DIR', 'output'),
            start_date=start_date,
            end_date=end_date,
            rate_limit_calls=int(os.getenv('TWITTER_RATE_LIMIT_CALLS', '30')),
            rate_limit_period=int(os.getenv('TWITTER_RATE_LIMIT_PERIOD', '60')),
            request_timeout=int(os.getenv('TWITTER_REQUEST_TIMEOUT', '30')),
            retry_attempts=int(os.getenv('TWITTER_RETRY_ATTEMPTS', '3')),
            retry_delay=int(os.getenv('TWITTER_RETRY_DELAY', '5')),
            output_format=os.getenv('TWITTER_OUTPUT_FORMAT', 'csv'),
            add_metadata=os.getenv('TWITTER_ADD_METADATA', 'true').lower() == 'true',
            api_keys=api_keys,
            api_key_rotation=os.getenv('TWITTER_API_KEY_ROTATION', 'sequential'),
            proxy_url=os.getenv('TWITTER_PROXY_URL'),
            user_agent=os.getenv('TWITTER_USER_AGENT', 'SocialScope-Tweets/1.0'),
            export_formats=os.getenv('TWITTER_EXPORT_FORMATS', 'csv').split(',')
        )
    
    @classmethod
    def load_profile(cls, profile_name: str) -> 'ScraperConfig':
        """Load configuration from a saved profile"""
        profile_path = Path('profiles') / f"{profile_name}.json"
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {profile_name}")
        
        with open(profile_path, 'r', encoding='utf-8') as f:
            profile_data = json.load(f)
        
        # Handle date conversion
        if 'start_date' in profile_data and profile_data['start_date']:
            profile_data['start_date'] = datetime.fromisoformat(profile_data['start_date'])
        if 'end_date' in profile_data and profile_data['end_date']:
            profile_data['end_date'] = datetime.fromisoformat(profile_data['end_date'])
        
        return cls(**profile_data)
    
    def save_profile(self, profile_name: str):
        """Save configuration as a profile"""
        # Create profiles directory if it doesn't exist
        profiles_dir = Path('profiles')
        profiles_dir.mkdir(exist_ok=True)
        
        # Convert to dict, handling datetime objects
        config_dict = asdict(self)
        if self.start_date:
            config_dict['start_date'] = self.start_date.isoformat()
        if self.end_date:
            config_dict['end_date'] = self.end_date.isoformat()
        
        # Save to file
        profile_path = profiles_dir / f"{profile_name}.json"
        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2)
        
        logging.info(f"Profile saved: {profile_name}")

class AdaptiveRateLimiter:
    """Advanced rate limiter with adaptive throttling"""
    def __init__(self, max_calls: int, period: int, burst_factor: float = 1.5):
        self.max_calls = max_calls
        self.period = period
        self.burst_factor = burst_factor
        self.calls = []
        self.error_timestamps = []  # Track rate limit errors
        self.dynamic_max_calls = max_calls  # This will adjust dynamically
        self._lock = threading.RLock()  # Thread-safe operation
        
    def wait_if_needed(self):
        """Wait if rate limit is reached with adaptive behavior"""
        with self._lock:
            now = time.time()
            
            # Clean up old calls and errors
            self.calls = [call for call in self.calls if call > now - self.period]
            self.error_timestamps = [ts for ts in self.error_timestamps if ts > now - (self.period * 5)]
            
            # Adjust rate limit based on recent errors
            if len(self.error_timestamps) > 0:
                # If we've seen rate limit errors, reduce our rate
                self.dynamic_max_calls = max(1, int(self.max_calls * 0.8))
            else:
                # Slowly increase back to max if no errors
                self.dynamic_max_calls = min(
                    self.max_calls,
                    self.dynamic_max_calls + 1 if len(self.calls) < self.dynamic_max_calls else self.dynamic_max_calls
                )
            
            # Calculate wait time if needed
            if len(self.calls) >= self.dynamic_max_calls:
                sleep_time = self.calls[0] - (now - self.period) + 0.1  # Add small buffer
                if sleep_time > 0:
                    logging.info(f"Rate limit reached. Waiting {sleep_time:.2f} seconds... (Current limit: {self.dynamic_max_calls}/{self.period}s)")
                    time.sleep(sleep_time)
            
            self.calls.append(now)
    
    def register_error(self):
        """Register a rate limit error to adjust behavior"""
        with self._lock:
            now = time.time()
            self.error_timestamps.append(now)
            # Immediately reduce rate limit after an error
            self.dynamic_max_calls = max(1, int(self.dynamic_max_calls * 0.7))
            logging.warning(f"Rate limit error registered. Adjusting rate to {self.dynamic_max_calls}/{self.period}s")

class ApiKeyManager:
    """Manage multiple API keys with rotation"""
    def __init__(self, keys: List[str], rotation_strategy: str = 'sequential'):
        self.keys = keys
        self.strategy = rotation_strategy
        self.current_index = 0
        self.usage_counts = {key: 0 for key in keys}
        self.rate_limits = {key: {'reset_time': 0, 'remaining': 120} for key in keys}
        self._lock = threading.RLock()
    
    def get_api_key(self) -> str:
        """Get the next API key based on strategy"""
        with self._lock:
            if not self.keys:
                raise ValueError("No API keys available")
            
            if self.strategy == 'sequential':
                key = self._get_sequential_key()
            elif self.strategy == 'least_used':
                key = self._get_least_used_key()
            elif self.strategy == 'rate_limit_aware':
                key = self._get_rate_limit_aware_key()
            else:
                raise ValueError(f"Unknown rotation strategy: {self.strategy}")
            
            self.usage_counts[key] += 1
            return key
    
    def _get_sequential_key(self) -> str:
        """Get next key in sequence"""
        key = self.keys[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.keys)
        return key
    
    def _get_least_used_key(self) -> str:
        """Get least used key"""
        return min(self.usage_counts.items(), key=lambda x: x[1])[0]
    
    def _get_rate_limit_aware_key(self) -> str:
        """Get key with most remaining capacity"""
        now = time.time()
        for key, limit_info in self.rate_limits.items():
            if now > limit_info['reset_time']:
                # Reset the counter if the reset time has passed
                limit_info['remaining'] = 120
                limit_info['reset_time'] = now + 60  # Reset after 1 minute
        
        # Get key with highest remaining capacity
        best_key = max(self.rate_limits.items(), key=lambda x: x[1]['remaining'])[0]
        self.rate_limits[best_key]['remaining'] -= 1
        return best_key
    
    def update_rate_limit(self, key: str, remaining: int, reset_time: int):
        """Update rate limit information for a key"""
        with self._lock:
            if key in self.rate_limits:
                self.rate_limits[key]['remaining'] = remaining
                self.rate_limits[key]['reset_time'] = reset_time

class TwitterQueryBuilder:
    """Helper class to build complex Twitter search queries"""
    
    def __init__(self):
        self._query_parts = []
    
    def from_user(self, username: str) -> 'TwitterQueryBuilder':
        """Tweets from a specific user"""
        self._query_parts.append(f"from:{username}")
        return self
    
    def to_user(self, username: str) -> 'TwitterQueryBuilder':
        """Tweets to a specific user"""
        self._query_parts.append(f"to:{username}")
        return self
    
    def mentioning(self, username: str) -> 'TwitterQueryBuilder':
        """Tweets mentioning a specific user"""
        self._query_parts.append(f"@{username}")
        return self
    
    def exclude_replies(self) -> 'TwitterQueryBuilder':
        """Exclude replies"""
        self._query_parts.append("-filter:replies")
        return self
    
    def only_replies(self) -> 'TwitterQueryBuilder':
        """Only include replies"""
        self._query_parts.append("filter:replies")
        return self
    
    def min_retweets(self, count: int) -> 'TwitterQueryBuilder':
        """Tweets with minimum number of retweets"""
        self._query_parts.append(f"min_retweets:{count}")
        return self
    
    def min_likes(self, count: int) -> 'TwitterQueryBuilder':
        """Tweets with minimum number of likes"""
        self._query_parts.append(f"min_faves:{count}")
        return self
    
    def min_replies(self, count: int) -> 'TwitterQueryBuilder':
        """Tweets with minimum number of replies"""
        self._query_parts.append(f"min_replies:{count}")
        return self
    
    def since_date(self, date: datetime) -> 'TwitterQueryBuilder':
        """Tweets since date (inclusive)"""
        timestamp = int(date.timestamp())
        self._query_parts.append(f"since_time:{timestamp}")
        return self
    
    def until_date(self, date: datetime) -> 'TwitterQueryBuilder':
        """Tweets before date (not inclusive)"""
        timestamp = int(date.timestamp())
        self._query_parts.append(f"until_time:{timestamp}")
        return self
    
    def has_media(self) -> 'TwitterQueryBuilder':
        """Tweets containing media"""
        self._query_parts.append("filter:media")
        return self
    
    def has_images(self) -> 'TwitterQueryBuilder':
        """Tweets containing images"""
        self._query_parts.append("filter:images")
        return self
    
    def has_videos(self) -> 'TwitterQueryBuilder':
        """Tweets containing videos"""
        self._query_parts.append("filter:videos")
        return self
    
    def has_links(self) -> 'TwitterQueryBuilder':
        """Tweets containing links"""
        self._query_parts.append("filter:links")
        return self
    
    def is_verified(self) -> 'TwitterQueryBuilder':
        """Tweets from verified users"""
        self._query_parts.append("filter:blue_verified")
        return self
    
    def keyword(self, text: str) -> 'TwitterQueryBuilder':
        """Add a keyword to search for"""
        self._query_parts.append(text)
        return self
    
    def exclude_keyword(self, text: str) -> 'TwitterQueryBuilder':
        """Exclude a keyword from search"""
        self._query_parts.append(f"-{text}")
        return self
    
    def build(self) -> str:
        """Build the final query string"""
        return " ".join(self._query_parts)

class EnhancedTwitterScraper:
    """Enhanced Twitter scraper implementation"""
    
    def __init__(self, config: ScraperConfig):
        """Initialize scraper with configuration"""
        self.config = config
        self.setup_api_keys()
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json',
            'User-Agent': self.config.user_agent
        }
        self.rate_limiter = AdaptiveRateLimiter(
            self.config.rate_limit_calls,
            self.config.rate_limit_period
        )
        self.setup_directories()
        self.user_id = None
        self.seen_tweets: Set[str] = set()
        self.session = self.setup_session()
    
    def setup_api_keys(self):
        """Set up API key management"""
        if self.config.api_keys:
            self.key_manager = ApiKeyManager(self.config.api_keys, self.config.api_key_rotation)
            self.api_key = self.key_manager.get_api_key()
        else:
            self.api_key = self.get_api_key()
            self.key_manager = None
    
    def setup_session(self):
        """Set up requests session with proxy support"""
        session = requests.Session()
        
        # Configure proxy if specified
        if self.config.proxy_url:
            session.proxies = {
                'http': self.config.proxy_url,
                'https': self.config.proxy_url
            }
        
        return session
    
    def setup_directories(self):
        """Create necessary directories"""
        for directory in ['logs', 'output', 'cache', 'profiles']:
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
        """Make API request with enhanced retry logic and rate limiting"""
        last_exception = None
        backoff_factor = 1.5
        
        for attempt in range(self.config.retry_attempts):
            try:
                self.rate_limiter.wait_if_needed()
                
                # If using multiple API keys, rotate them
                if self.key_manager and attempt > 0:
                    self.api_key = self.key_manager.get_api_key()
                    self.headers['Authorization'] = f'Bearer {self.api_key}'
                
                # Log request intent (but mask API key)
                masked_url = url
                logging.debug(f"Requesting: {masked_url} (Attempt {attempt + 1}/{self.config.retry_attempts})")
                
                response = self.session.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=self.config.request_timeout
                )
                
                # Handle rate limit information
                remaining = response.headers.get('X-Rate-Limit-Remaining')
                reset = response.headers.get('X-Rate-Limit-Reset')
                
                if remaining and reset and self.key_manager:
                    self.key_manager.update_rate_limit(
                        self.api_key, 
                        int(remaining), 
                        int(reset)
                    )
                
                # Handle specific status codes
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # Validate response format
                        if not self._validate_response(data):
                            raise ValueError("Invalid response format")
                        return data
                    except json.JSONDecodeError:
                        raise ValueError(f"Invalid JSON response: {response.text[:100]}...")
                elif response.status_code == 429:  # Rate limit
                    self.rate_limiter.register_error()
                    wait_time = int(response.headers.get('Retry-After', self.config.retry_delay))
                    logging.warning(f"Rate limit hit. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                elif response.status_code == 401:  # Auth issue
                    raise AuthenticationError("Invalid API key or authentication error")
                elif response.status_code == 404:  # Not found
                    raise ResourceNotFoundError(f"Resource not found: {url}")
                elif response.status_code == 500:  # Server error
                    logging.error(f"Server error: {response.text}")
                    time.sleep(self.config.retry_delay * (backoff_factor ** attempt))
                else:
                    logging.error(f"HTTP Error {response.status_code}: {response.text}")
                    time.sleep(self.config.retry_delay * (backoff_factor ** attempt))
                    
            except (requests.Timeout, requests.ConnectionError) as e:
                wait_time = self.config.retry_delay * (backoff_factor ** attempt)
                logging.warning(f"Network error: {e}. Retrying in {wait_time:.1f} seconds... (Attempt {attempt + 1}/{self.config.retry_attempts})")
                time.sleep(wait_time)
                last_exception = e
            except (ValueError, json.JSONDecodeError, requests.RequestException) as e:
                logging.error(f"Request failed: {e} (Attempt {attempt + 1}/{self.config.retry_attempts})")
                last_exception = e
                
                if attempt < self.config.retry_attempts - 1:
                    wait_time = self.config.retry_delay * (backoff_factor ** attempt)
                    time.sleep(wait_time)
        
        # If we get here, all retries failed
        if last_exception:
            raise ScraperException(f"Max retry attempts reached. Last error: {str(last_exception)}")
        else:
            raise ScraperException("Max retry attempts reached for an unknown reason")

    def _validate_response(self, data: Dict) -> bool:
        """Validate response has expected format"""
        if not isinstance(data, dict):
            return False
            
        # Tweets response validation
        if 'tweets' in data:
            return isinstance(data['tweets'], list)
            
        # User response validation
        if 'id_str' in data and 'screen_name' in data:
            return True
            
        # Search response validation  
        if 'next_cursor' in data:
            return True
            
        return True  # Default to true for other response types

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
            
        return self.fetch_tweets_for_query(query, progress_callback)

    def fetch_tweets_for_query(self, query: str, progress_callback: Callable[[float, str, bool], None] = None) -> List[Dict]:
        """Fetch tweets for a single query string"""
        all_tweets = []
        cursor = None
        consecutive_errors = 0
        
        try:
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
            if progress_callback:
                progress_callback(100, f"Error: {str(e)}", True)
            return all_tweets

    def fetch_multiple_queries(self, queries: List[str], max_workers: int = 3) -> Dict[str, List[Dict]]:
        """
        Fetch tweets for multiple queries in parallel
        
        Args:
            queries: List of search queries to run
            max_workers: Maximum number of parallel workers
            
        Returns:
            Dict mapping query strings to lists of tweets
        """
        import concurrent.futures
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all fetch tasks
            future_to_query = {
                executor.submit(self.fetch_tweets_for_query, query): query 
                for query in queries
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    tweets = future.result()
                    results[query] = tweets
                    logging.info(f"Completed fetch for query '{query}': {len(tweets)} tweets")
                except Exception as e:
                    logging.error(f"Error fetching query '{query}': {e}")
                    results[query] = []
        
        return results

    def save_tweets(self, tweets: List[Dict], format: str = None, add_metadata: bool = None) -> str:
        """
        Save tweets to a file in various formats
        
        Args:
            tweets: List of tweets to save
            format: Output format - 'csv', 'json', or 'sqlite'
            add_metadata: Whether to add metadata about the query
                
        Returns:
            Path to saved file or empty string on failure
        """
        if not tweets:
            return ""

        try:
            # Use format from parameters, or fallback to config
            format = format or self.config.output_format
            add_metadata = add_metadata if add_metadata is not None else self.config.add_metadata
            
            # Create filename with details
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            tweet_type = {
                'tweets': 'tweets_only',
                'replies': 'replies_only',
                'both': 'tweets_and_replies'
            }.get(self.config.scrape_type, 'tweets')
            
            base_filename = f'{self.config.username}_{tweet_type}_{timestamp}_{len(tweets)}_tweets'
            output_dir = Path(self.config.save_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Add metadata if requested
            metadata = {}
            if add_metadata:
                metadata = {
                    'username': self.config.username,
                    'scrape_type': self.config.scrape_type,
                    'tweet_count': len(tweets),
                    'timestamp': timestamp,
                    'query_params': {
                        'max_tweets': self.config.max_tweets,
                        'start_date': self.config.start_date.isoformat() if self.config.start_date else None,
                        'end_date': self.config.end_date.isoformat() if self.config.end_date else None
                    }
                }
            
            # Save in the requested format
            if format.lower() == 'csv':
                filename = output_dir / f'{base_filename}.csv'
                logging.info(f"Saving tweets to CSV: {filename}")
                return self._save_as_csv(tweets, filename, metadata)
                
            elif format.lower() == 'json':
                filename = output_dir / f'{base_filename}.json'
                logging.info(f"Saving tweets to JSON: {filename}")
                return self._save_as_json(tweets, filename, metadata)
                
            elif format.lower() == 'sqlite':
                filename = output_dir / f'{base_filename}.db'
                logging.info(f"Saving tweets to SQLite: {filename}")
                return self._save_as_sqlite(tweets, filename, metadata)
                
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logging.error(f"Error saving tweets: {str(e)}")
            return ""

    def _save_as_csv(self, tweets: List[Dict], filename: Path, metadata: Dict) -> str:
        """Save tweets to CSV file"""
        fieldnames = [
            'tweet_id', 'created_at', 'text', 'likes', 'retweets',
            'quotes', 'views', 'replies', 'is_reply', 'is_retweet',
            'media_count', 'hashtags', 'mentions', 'urls', 'author_username',
            'author_name', 'author_followers', 'author_verified'
        ]
        
        # Create parent directory if it doesn't exist
        filename.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for tweet in tweets:
                user = tweet.get('user', {})
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
                    'urls': ','.join(u['expanded_url'] for u in tweet.get('entities', {}).get('urls', [])),
                    'author_username': user.get('screen_name'),
                    'author_name': user.get('name'),
                    'author_followers': user.get('followers_count'),
                    'author_verified': user.get('verified')
                })
        
        # If requested, save metadata to a separate file
        if metadata:
            meta_filename = filename.with_name(f"{filename.stem}_metadata.json")
            with open(meta_filename, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
        
        return str(filename)

    def _save_as_json(self, tweets: List[Dict], filename: Path, metadata: Dict) -> str:
        """Save tweets to JSON file"""
        # Add metadata to the output structure
        output = {
            'metadata': metadata,
            'tweets': tweets
        }
        
        # Create parent directory if it doesn't exist
        filename.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        return str(filename)

    def _save_as_sqlite(self, tweets: List[Dict], filename: Path, metadata: Dict) -> str:
        """Save tweets to SQLite database"""
        import sqlite3
        
        # Create parent directory if it doesn't exist
        filename.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(str(filename))
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE tweets (
            tweet_id TEXT PRIMARY KEY,
            created_at TEXT,
            text TEXT,
            likes INTEGER,
            retweets INTEGER,
            quotes INTEGER,
            views INTEGER,
            replies INTEGER,
            is_reply INTEGER,
            is_retweet INTEGER,
            media_count INTEGER,
            hashtags TEXT,
            mentions TEXT,
            urls TEXT,
            author_username TEXT,
            author_name TEXT,
            author_followers INTEGER,
            author_verified INTEGER
        )
        ''')
        
        # Save metadata
        if metadata:
            flattened_metadata = self._flatten_dict(metadata)
            for key, value in flattened_metadata.items():
                cursor.execute("INSERT INTO metadata VALUES (?, ?)", (key, str(value)))
        
        # Save tweets
        for tweet in tweets:
            user = tweet.get('user', {})
            cursor.execute(
                "INSERT INTO tweets VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    tweet.get('id_str'),
                    tweet.get('tweet_created_at'),
                    tweet.get('full_text'),
                    tweet.get('favorite_count'),
                    tweet.get('retweet_count'),
                    tweet.get('quote_count'),
                    tweet.get('views_count'),
                    tweet.get('reply_count'),
                    1 if tweet.get('in_reply_to_status_id_str') else 0,
                    1 if tweet.get('retweeted_status') else 0,
                    len(tweet.get('media', [])),
                    ','.join(h['text'] for h in tweet.get('entities', {}).get('hashtags', [])),
                    ','.join(m['screen_name'] for m in tweet.get('entities', {}).get('user_mentions', [])),
                    ','.join(u['expanded_url'] for u in tweet.get('entities', {}).get('urls', [])),
                    user.get('screen_name'),
                    user.get('name'),
                    user.get('followers_count'),
                    1 if user.get('verified') else 0
                )
            )
        
        conn.commit()
        conn.close()
        
        return str(filename)
        
    def _flatten_dict(self, d, parent_key='', sep='_'):
        """Flatten nested dictionary for SQLite storage"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def analyze_tweets(self, tweets: List[Dict]) -> Dict:
        """
        Analyze a collection of tweets to extract insights
        
        Args:
            tweets: List of tweet objects
            
        Returns:
            Dict containing analysis results
        """
        if not tweets:
            return {"error": "No tweets to analyze"}
        
        # Basic statistics
        engagement = {
            'total_likes': sum(tweet.get('favorite_count', 0) or 0 for tweet in tweets),
            'total_retweets': sum(tweet.get('retweet_count', 0) or 0 for tweet in tweets),
            'total_replies': sum(tweet.get('reply_count', 0) or 0 for tweet in tweets),
            'total_quotes': sum(tweet.get('quote_count', 0) or 0 for tweet in tweets),
            'total_views': sum(tweet.get('views_count', 0) or 0 for tweet in tweets),
            'average_likes': sum(tweet.get('favorite_count', 0) or 0 for tweet in tweets) / max(len(tweets), 1),
            'average_retweets': sum(tweet.get('retweet_count', 0) or 0 for tweet in tweets) / max(len(tweets), 1),
        }
        
        # Most engaging tweets
        top_liked = sorted(tweets, key=lambda t: t.get('favorite_count', 0) or 0, reverse=True)[:5]
        top_retweeted = sorted(tweets, key=lambda t: t.get('retweet_count', 0) or 0, reverse=True)[:5]
        
        # Extract hashtags
        all_hashtags = []
        for tweet in tweets:
            hashtags = tweet.get('entities', {}).get('hashtags', [])
            all_hashtags.extend([h['text'].lower() for h in hashtags])
        
        hashtag_counts = {}
        for tag in all_hashtags:
            hashtag_counts[tag] = hashtag_counts.get(tag, 0) + 1
        
        top_hashtags = sorted(hashtag_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Extract mentions
        all_mentions = []
        for tweet in tweets:
            mentions = tweet.get('entities', {}).get('user_mentions', [])
            all_mentions.extend([m['screen_name'] for m in mentions])
        
        mention_counts = {}
        for mention in all_mentions:
            mention_counts[mention] = mention_counts.get(mention, 0) + 1
        
        top_mentions = sorted(mention_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Extract domains from URLs
        all_domains = []
        for tweet in tweets:
            urls = tweet.get('entities', {}).get('urls', [])
            for url_obj in urls:
                expanded_url = url_obj.get('expanded_url', '')
                if expanded_url:
                    try:
                        domain = urlparse(expanded_url).netloc
                        all_domains.append(domain)
                    except:
                        pass
        
        domain_counts = {}
        for domain in all_domains:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        top_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Time-based analysis
        tweet_times = []
        for tweet in tweets:
            created_at = tweet.get('tweet_created_at')
            if created_at:
                try:
                    if 'Z' in created_at:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    else:
                        dt = datetime.fromisoformat(created_at)
                    tweet_times.append(dt)
                except:
                    # Fallback for other date formats
                    try:
                        dt = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%S.%f%z')
                        tweet_times.append(dt)
                    except:
                        pass
        
        # Activity by hour of day
        hour_activity = {}
        for dt in tweet_times:
            hour = dt.hour
            hour_activity[hour] = hour_activity.get(hour, 0) + 1
        
        # Activity by day of week
        day_activity = {}
        for dt in tweet_times:
            day = dt.strftime('%A')
            day_activity[day] = day_activity.get(day, 0) + 1
        
        return {
            'tweet_count': len(tweets),
            'engagement': engagement,
            'top_liked_tweets': [{
                'id': t.get('id_str'),
                'text': t.get('full_text', '')[:100] + ('...' if len(t.get('full_text', '')) > 100 else ''),
                'likes': t.get('favorite_count'),
                'retweets': t.get('retweet_count')
            } for t in top_liked],
            'top_retweeted_tweets': [{
                'id': t.get('id_str'),
                'text': t.get('full_text', '')[:100] + ('...' if len(t.get('full_text', '')) > 100 else ''),
                'likes': t.get('favorite_count'),
                'retweets': t.get('retweet_count')
            } for t in top_retweeted],
            'hashtag_analysis': {
                'total_hashtags': len(all_hashtags),
                'unique_hashtags': len(hashtag_counts),
                'top_hashtags': top_hashtags
            },
            'mention_analysis': {
                'total_mentions': len(all_mentions),
                'unique_mentions': len(mention_counts),
                'top_mentions': top_mentions
            },
            'url_analysis': {
                'total_urls': len(all_domains),
                'unique_domains': len(domain_counts),
                'top_domains': top_domains
            },
            'time_analysis': {
                'hour_activity': hour_activity,
                'day_activity': day_activity
            }
        }

    def stream_tweets(self, callback: Callable[[Dict], None], query: str = None, max_duration: int = 3600):
        """
        Stream tweets in real-time with callback processing
        
        Args:
            callback: Function to call for each tweet
            query: Optional search query
            max_duration: Maximum duration in seconds to stream
        """
        if not query:
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
        
        logging.info(f"Starting tweet streaming with query: {query}")
        
        cursor = None
        processed_count = 0
        start_time = time.time()
        
        try:
            while time.time() - start_time < max_duration and processed_count < self.config.max_tweets:
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
                        break
                    
                    # Process tweets
                    for tweet in tweets:
                        tweet_id = tweet.get('id_str')
                        if tweet_id and tweet_id not in self.seen_tweets:
                            self.seen_tweets.add(tweet_id)
                            callback(tweet)
                            processed_count += 1
                            
                            if processed_count >= self.config.max_tweets:
                                logging.info(f"Reached target of {self.config.max_tweets} tweets")
                                break
                    
                    # Get next cursor
                    cursor = data.get('next_cursor')
                    if not cursor:
                        logging.info("No more pages available")
                        break
                    
                    # Small delay between requests
                    time.sleep(0.5)
                    
                except Exception as e:
                    logging.error(f"Error during tweet streaming: {str(e)}")
                    time.sleep(self.config.retry_delay)
            
            logging.info(f"Tweet streaming completed. Total tweets processed: {processed_count}")
            
        except KeyboardInterrupt:
            logging.info("Tweet streaming interrupted by user")
        except Exception as e:
            logging.error(f"Fatal error during tweet streaming: {str(e)}")