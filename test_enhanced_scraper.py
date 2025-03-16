# test_enhanced_scraper.py
#!/usr/bin/env python3
from enhanced_scraper import EnhancedTwitterScraper, ScraperConfig, TwitterQueryBuilder
from datetime import datetime, timedelta
import logging
import os
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def basic_usage_test():
    """Demonstrate basic usage of the enhanced scraper"""
    print("\n=== Basic Usage Test ===")
    
    # Load API key from .env
    load_dotenv()
    
    # Create configuration
    config = ScraperConfig(
        username="elonmusk",
        max_tweets=10,  # Just a few for testing
        scrape_type="both",
        save_dir="output/test"
    )
    
    # Create scraper
    scraper = EnhancedTwitterScraper(config)
    
    # Verify account
    print("Verifying account...")
    account_info = scraper.verify_account()
    
    if not account_info['success']:
        print(f"Error: {account_info.get('error')}")
        return
    
    print(f"Account: {account_info['name']} (@{config.username})")
    print(f"Tweets: {account_info['total_tweets']:,}")
    print(f"Followers: {account_info['followers']:,}")
    
    # Fetch tweets
    print("\nFetching tweets...")
    tweets = scraper.fetch_tweets()
    
    print(f"Fetched {len(tweets)} tweets")
    
    # Save in different formats
    for fmt in ['csv', 'json']:
        filename = scraper.save_tweets(tweets, format=fmt)
        print(f"Saved to {filename}")
    
    # Analyze tweets
    print("\nAnalyzing tweets...")
    analysis = scraper.analyze_tweets(tweets)
    
    print(f"Total engagement: {analysis['engagement']['total_likes']} likes, {analysis['engagement']['total_retweets']} retweets")
    if analysis['hashtag_analysis']['top_hashtags']:
        print("Top hashtags:", ', '.join(f"#{tag}" for tag, _ in analysis['hashtag_analysis']['top_hashtags'][:3]))

def query_builder_test():
    """Demonstrate query builder usage"""
    print("\n=== Query Builder Test ===")
    
    # Load API key from .env
    load_dotenv()
    
    # Create configuration
    config = ScraperConfig(
        username="",  # Not needed for custom query
        max_tweets=10,  # Just a few for testing
        save_dir="output/test_query"
    )
    
    # Create scraper
    scraper = EnhancedTwitterScraper(config)
    
    # Create query
    builder = TwitterQueryBuilder()
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    query = (builder
        .from_user("elonmusk")
        .min_likes(1000)
        .since_date(week_ago)
        .build()
    )
    
    print(f"Query: {query}")
    
    # Fetch tweets
    print("\nFetching tweets for query...")
    tweets = scraper.fetch_tweets_for_query(query)
    
    print(f"Fetched {len(tweets)} tweets")
    
    # Save in CSV format
    if tweets:
        filename = scraper.save_tweets(tweets, format='csv')
        print(f"Saved to {filename}")

def multiple_queries_test():
    """Demonstrate multiple queries"""
    print("\n=== Multiple Queries Test ===")
    
    # Load API key from .env
    load_dotenv()
    
    # Create configuration
    config = ScraperConfig(
        username="",  # Not needed for custom queries
        max_tweets=5,  # Just a few for testing
        save_dir="output/test_multi"
    )
    
    # Create scraper
    scraper = EnhancedTwitterScraper(config)
    
    # Define queries
    queries = [
        "from:elonmusk min_faves:5000",
        "from:narendramodi min_faves:5000",
        "from:NASA has:images"
    ]
    
    print(f"Running {len(queries)} queries...")
    
    # Fetch tweets for all queries
    results = scraper.fetch_multiple_queries(queries)
    
    # Print results
    for query, tweets in results.items():
        print(f"Query '{query}': {len(tweets)} tweets")
        
    # Combine and save all tweets
    all_tweets = []
    for tweets in results.values():
        all_tweets.extend(tweets)
    
    if all_tweets:
        filename = scraper.save_tweets(all_tweets, format='json')
        print(f"Saved {len(all_tweets)} tweets to {filename}")

def main():
    """Run all tests"""
    print("Testing Enhanced Twitter Scraper...")
    
    basic_usage_test()
    query_builder_test()
    multiple_queries_test()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main()