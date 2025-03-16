"""
SocialData API Client - Core module for interacting with the SocialData API
"""

import os
import time
import logging
import requests
from typing import Dict, List, Optional, Union, Any
from pathlib import Path
from dotenv import load_dotenv

class RateLimiter:
    """Handles rate limiting for API requests"""
    
    def __init__(self, max_calls: int = 30, period: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_calls: Maximum number of calls allowed in the period
            period: Time period in seconds
        """
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


class SocialDataClient:
    """Client for interacting with the SocialData API"""
    
    BASE_URL = "https://api.socialdata.tools"
    
    def __init__(self, api_key: Optional[str] = None, rate_limit_calls: int = 30, 
                 rate_limit_period: int = 60, retry_attempts: int = 3, retry_delay: int = 5):
        """
        Initialize the SocialData API client
        
        Args:
            api_key: SocialData API key (if None, loaded from .env file)
            rate_limit_calls: Maximum API calls per rate limit period
            rate_limit_period: Rate limit period in seconds
            retry_attempts: Number of retry attempts for failed requests
            retry_delay: Delay between retry attempts in seconds
        """
        self.api_key = api_key or self._load_api_key()
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json'
        }
        self.rate_limiter = RateLimiter(rate_limit_calls, rate_limit_period)
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
        )
    
    def _load_api_key(self) -> str:
        """Load API key from .env file"""
        load_dotenv()
        api_key = os.getenv('SOCIALDATA_API_KEY') or os.getenv('TWITTER_API_KEY')
        
        if not api_key:
            raise ValueError("API key not found. Please set SOCIALDATA_API_KEY in .env file.")
        
        return api_key
    
    def make_request(self, endpoint: str, method: str = "GET", 
                    params: Optional[Dict] = None, json_data: Optional[Dict] = None) -> Dict:
        """
        Make an API request with retry logic and rate limiting
        
        Args:
            endpoint: API endpoint (without base URL)
            method: HTTP method (GET, POST, etc.)
            params: URL parameters
            json_data: JSON data for POST requests
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"
        
        for attempt in range(self.retry_attempts):
            try:
                self.rate_limiter.wait_if_needed()
                
                response = requests.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=json_data,
                    timeout=30
                )
                
                # Handle HTTP errors
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:  # Rate limit exceeded
                    wait_time = int(response.headers.get('Retry-After', self.retry_delay))
                    logging.warning(f"Rate limit hit. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 402:  # Payment Required
                    raise Exception("SocialData API: Not enough credits to perform this request")
                elif response.status_code == 404:  # Not Found
                    raise Exception(f"SocialData API: Resource not found. Response: {response.text}")
                else:
                    response.raise_for_status()
                    
            except requests.Timeout:
                logging.warning(f"Request timeout (attempt {attempt + 1}/{self.retry_attempts})")
            except requests.RequestException as e:
                logging.error(f"Request failed: {e} (attempt {attempt + 1}/{self.retry_attempts})")
            
            # If we get here, the request failed and we should retry
            if attempt < self.retry_attempts - 1:
                time.sleep(self.retry_delay)
        
        raise Exception(f"Max retry attempts reached for endpoint: {endpoint}")
    
    def get_user_info(self, username: str) -> Dict:
        """
        Get user information by username
        
        Args:
            username: Twitter username (without @)
            
        Returns:
            User information as dictionary
        """
        return self.make_request(f"twitter/user/{username}")
    
    def get_user_tweets(self, user_id: str, include_replies: bool = True, cursor: Optional[str] = None) -> Dict:
        """
        Get tweets for a user
        
        Args:
            user_id: Twitter user ID
            include_replies: Whether to include replies
            cursor: Pagination cursor
            
        Returns:
            Dictionary with tweets and cursor
        """
        endpoint = f"twitter/user/{user_id}/tweets"
        if include_replies:
            endpoint = f"twitter/user/{user_id}/tweets-and-replies"
        
        params = {}
        if cursor:
            params['cursor'] = cursor
            
        return self.make_request(endpoint, params=params)
    
    def search_tweets(self, query: str, search_type: str = "Latest", cursor: Optional[str] = None) -> Dict:
        """
        Search for tweets
        
        Args:
            query: Search query with operators
            search_type: "Latest" or "Top"
            cursor: Pagination cursor
            
        Returns:
            Dictionary with tweets and cursor
        """
        params = {
            'query': query,
            'type': search_type
        }
        
        if cursor:
            params['cursor'] = cursor
            
        return self.make_request("twitter/search", params=params)

    def get_tweet(self, tweet_id: str) -> Dict:
        """
        Get a single tweet by ID
        
        Args:
            tweet_id: Twitter tweet ID
            
        Returns:
            Tweet data as dictionary
        """
        return self.make_request(f"twitter/tweets/{tweet_id}")


# For direct script execution
if __name__ == "__main__":
    client = SocialDataClient()
    # Simple test
    try:
        user = client.get_user_info("elonmusk")
        print(f"Found user: {user['name']} (@{user['screen_name']})")
        print(f"Followers: {user['followers_count']:,}")
    except Exception as e:
        print(f"Error: {e}")