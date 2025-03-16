#!/usr/bin/env python3
"""
Tweet Counter - Script for counting tweets and replies
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Add src directory to the Python path
sys.path.append(PROJECT_ROOT)

# Import directly from the modules
from src.core.socialdata_client import SocialDataClient
from src.core.tweet_fetcher import TweetFetcher

def main():
    """Main function"""
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Count tweets and replies')
    
    parser.add_argument('username', help='Twitter username (without @)')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Initialize components
    client = SocialDataClient()
    fetcher = TweetFetcher(client)
    
    try:
        # Fetch account info
        logger.info(f"Fetching account info for @{args.username}")
        result = fetcher.count_user_tweets(args.username)
        
        account_info = result['user_info']
        total_count = result['total']
        
        # Display results
        print("\n=== Account Information ===")
        print(f"Username: @{account_info['screen_name']}")
        print(f"Name: {account_info['name']}")
        print(f"Account created: {account_info['created_at']}")
        print(f"Location: {account_info.get('location', 'N/A')}")
        print(f"Bio: {account_info.get('description', 'N/A')}")
        print("\n=== Tweet Statistics ===")
        print(f"Total tweets and replies: {total_count:,}")
        print(f"Followers: {account_info['followers_count']:,}")
        print(f"Following: {account_info['friends_count']:,}")
        print(f"Listed count: {account_info['listed_count']:,}")
        
        print("\nNote: To get a breakdown of tweets vs. replies, use the tweet_analyzer.py script")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())