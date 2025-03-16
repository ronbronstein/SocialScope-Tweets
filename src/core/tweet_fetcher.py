"""
Tweet Fetcher - Module for fetching tweets using the SocialData API
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Tuple, Any, Set
from pathlib import Path

from .socialdata_client import SocialDataClient

class TweetFetcher:
    """Class for fetching tweets with various filtering options"""
    
    def __init__(self, client: Optional[SocialDataClient] = None):
        """
        Initialize the tweet fetcher
        
        Args:
            client: SocialData API client (if None, a new one will be created)
        """
        self.client = client or SocialDataClient()
        self.logger = logging.getLogger(__name__)
    
    def fetch_user_info(self, username: str) -> Dict:
        """
        Fetch user information
        
        Args:
            username: Twitter username (without @)
            
        Returns:
            User information as dictionary
        """
        self.logger.info(f"Fetching user info for @{username}")
        return self.client.get_user_info(username)
    
    def fetch_user_tweets(self, username: str, 
                         tweet_type: str = "both", 
                         max_tweets: int = 1000,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None,
                         progress_callback: Optional[Callable[[float, str, bool], None]] = None) -> List[Dict]:
        """
        Fetch tweets for a user with filtering options
        
        Args:
            username: Twitter username (without @)
            tweet_type: "tweets", "replies", or "both"
            max_tweets: Maximum number of tweets to fetch
            start_date: Start date for tweet filtering
            end_date: End date for tweet filtering
            progress_callback: Callback for progress updates
            
        Returns:
            List of tweets
        """
        # First get user info to get the user_id
        user_info = self.fetch_user_info(username)
        user_id = user_info['id_str']
        
        # Build query based on parameters
        include_replies = tweet_type in ["replies", "both"]
        only_tweets = tweet_type == "tweets"
        
        # Build query string if using search endpoint
        query = ""
        if only_tweets:
            query = f"from:{username} -filter:replies"
        elif tweet_type == "replies":
            query = f"from:{username} filter:replies"
        else:  # both
            query = f"from:{username}"
            
        # Add date range to query if specified
        if start_date:
            start_timestamp = int(start_date.timestamp())
            query += f" since_time:{start_timestamp}"
        if end_date:
            end_timestamp = int(end_date.timestamp())
            query += f" until_time:{end_timestamp}"
            
        # Print info about the fetch
        self.logger.info(f"Fetching tweets for @{username} (User ID: {user_id})")
        self.logger.info(f"Type: {tweet_type}, Max tweets: {max_tweets}")
        if start_date:
            self.logger.info(f"Start date: {start_date.strftime('%Y-%m-%d')}")
        if end_date:
            self.logger.info(f"End date: {end_date.strftime('%Y-%m-%d')}")
            
        # Two approaches: 
        # 1. For "both" or specific type with date filtering: use search endpoint
        # 2. For specific type without date filtering: use user tweets endpoint
        
        # Initialize variables
        all_tweets = []
        seen_tweet_ids = set()
        cursor = None
        consecutive_errors = 0
        
        # Main fetch loop
        while len(all_tweets) < max_tweets:
            try:
                # Choose the right approach based on parameters
                if query:
                    # Search endpoint approach
                    data = self.client.search_tweets(query, cursor=cursor)
                else:
                    # User tweets endpoint approach
                    data = self.client.get_user_tweets(user_id, include_replies=include_replies, cursor=cursor)
                
                # Get tweets from response
                tweets = data.get('tweets', [])
                
                # Check if no tweets returned
                if not tweets:
                    self.logger.info("No more tweets available")
                    if progress_callback:
                        progress_callback(100, "Collection complete", True)
                    break
                
                # Process new tweets
                new_tweets_count = 0
                for tweet in tweets:
                    tweet_id = tweet.get('id_str')
                    if tweet_id and tweet_id not in seen_tweet_ids:
                        seen_tweet_ids.add(tweet_id)
                        all_tweets.append(tweet)
                        new_tweets_count += 1
                        
                        if len(all_tweets) >= max_tweets:
                            self.logger.info(f"Reached target of {max_tweets} tweets")
                            if progress_callback:
                                progress_callback(100, "Collection complete", True)
                            break
                
                # Update progress
                if progress_callback:
                    progress = min(100, (len(all_tweets) / max_tweets) * 100)
                    status = f"Collected {len(all_tweets):,} tweets"
                    is_complete = not cursor or len(all_tweets) >= max_tweets
                    progress_callback(progress, status, is_complete)
                
                # Log progress
                self.logger.info(f"Collected {new_tweets_count} new tweets (Total: {len(all_tweets)})")
                
                # Get next cursor
                cursor = data.get('next_cursor')
                if not cursor:
                    self.logger.info("No more pages available")
                    if progress_callback:
                        progress_callback(100, "Collection complete", True)
                    break
                
                # Reset error counter on successful request
                consecutive_errors = 0
                
                # Small delay between requests
                time.sleep(0.5)
            
            except Exception as e:
                consecutive_errors += 1
                self.logger.error(f"Error during tweet collection: {str(e)}")
                
                if consecutive_errors >= 3:  # Max retry attempts
                    self.logger.error("Max consecutive errors reached")
                    break
                
                time.sleep(2)  # Wait before retrying
        
        self.logger.info(f"Tweet collection completed. Total tweets: {len(all_tweets)}")
        return all_tweets
    
    def count_user_tweets(self, username: str) -> Dict[str, int]:
        """
        Count tweets, replies, and total tweets for a user
        
        Args:
            username: Twitter username (without @)
            
        Returns:
            Dict with counts for tweets, replies, and total
        """
        user_info = self.fetch_user_info(username)
        
        # The statuses_count gives us the total tweets+replies
        total_count = user_info.get('statuses_count', 0)
        
        # To get tweets vs replies breakdown, we'd need to fetch tweets
        # For now, return just the total from user info
        # For precise counts, you'd need to fetch and count
        
        return {
            'total': total_count,
            'user_info': user_info  # Include full user info for additional stats
        }