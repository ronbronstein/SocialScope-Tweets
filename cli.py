# cli.py
#!/usr/bin/env python3
import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from enhanced_scraper import EnhancedTwitterScraper, ScraperConfig, TwitterQueryBuilder
from dotenv import load_dotenv
import os

def setup_logging(verbose: int = 0):
    """Set up logging based on verbosity level"""
    log_level = logging.WARNING
    if verbose == 1:
        log_level = logging.INFO
    elif verbose >= 2:
        log_level = logging.DEBUG
    
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def main():
    """Main entry point for the command-line interface"""
    parser = argparse.ArgumentParser(description='SocialScope-Tweets - Enhanced Twitter scraper')
    
    # Basic options
    parser.add_argument('--username', '-u', help='Twitter username to scrape')
    parser.add_argument('--max-tweets', '-m', type=int, default=1000, help='Maximum number of tweets to collect')
    parser.add_argument('--type', '-t', choices=['tweets', 'replies', 'both'], default='both', help='Type of tweets to scrape')
    parser.add_argument('--output-dir', '-o', default='output', help='Directory to save output files')
    
    # Date options
    parser.add_argument('--start-date', '-s', help='Start date (MM/DD/YYYY)')
    parser.add_argument('--end-date', '-e', help='End date (MM/DD/YYYY)')
    
    # Output options
    parser.add_argument('--format', '-f', choices=['csv', 'json', 'sqlite', 'all'], default='csv', help='Output format')
    parser.add_argument('--no-metadata', action='store_true', help='Exclude metadata from output')
    
    # Advanced options
    parser.add_argument('--rate-limit-calls', type=int, default=30, help='Rate limit calls')
    parser.add_argument('--rate-limit-period', type=int, default=60, help='Rate limit period in seconds')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds')
    parser.add_argument('--retries', type=int, default=3, help='Number of retry attempts')
    parser.add_argument('--retry-delay', type=int, default=5, help='Delay between retries in seconds')
    parser.add_argument('--proxy', help='Proxy URL (e.g., socks5://127.0.0.1:9050)')
    
    # Profile options
    parser.add_argument('--load-profile', help='Load settings from a saved profile')
    parser.add_argument('--save-profile', help='Save settings to a profile')
    
    # Analysis options
    parser.add_argument('--analyze', action='store_true', help='Perform analysis on collected tweets')
    parser.add_argument('--stream', action='store_true', help='Stream tweets instead of batch collection')
    
    # Query options
    parser.add_argument('--query', '-q', help='Custom search query (overrides other filters)')
    
    # Multi-query option
    parser.add_argument('--queries-file', help='Path to file containing one query per line')
    
    # Verbosity
    parser.add_argument('--verbose', '-v', action='count', default=0, help='Increase verbosity')
    
    args = parser.parse_args()
    
    # Set up logging
    setup_logging(args.verbose)
    
    # Load environment variables
    load_dotenv()
    
    # Check if username is provided or in environment
    if not args.username and not args.load_profile and not args.query and not args.queries_file:
        username = os.getenv('TWITTER_USERNAME')
        if not username:
            parser.error("Username is required. Provide with --username or set TWITTER_USERNAME in .env file.")
        args.username = username
    
    # Handle profile
    config = None
    if args.load_profile:
        try:
            config = ScraperConfig.load_profile(args.load_profile)
            logging.info(f"Loaded profile: {args.load_profile}")
        except Exception as e:
            logging.error(f"Error loading profile: {e}")
            return 1
    else:
        # Parse dates
        start_date = None
        if args.start_date:
            try:
                start_date = datetime.strptime(args.start_date, '%m/%d/%Y')
            except ValueError:
                logging.error(f"Invalid start date format: {args.start_date}")
                return 1
        
        end_date = None
        if args.end_date:
            try:
                end_date = datetime.strptime(args.end_date, '%m/%d/%Y')
            except ValueError:
                logging.error(f"Invalid end date format: {args.end_date}")
                return 1
        
        # Create config from args
        export_formats = []
        if args.format == 'all':
            export_formats = ['csv', 'json', 'sqlite']
        else:
            export_formats = [args.format]
            
        config = ScraperConfig(
            username=args.username or '',
            max_tweets=args.max_tweets,
            scrape_type=args.type,
            save_dir=args.output_dir,
            start_date=start_date,
            end_date=end_date,
            rate_limit_calls=args.rate_limit_calls,
            rate_limit_period=args.rate_limit_period,
            request_timeout=args.timeout,
            retry_attempts=args.retries,
            retry_delay=args.retry_delay,
            output_format=args.format,
            add_metadata=not args.no_metadata,
            proxy_url=args.proxy,
            export_formats=export_formats
        )
    
    # Save profile if requested
    if args.save_profile:
        try:
            config.save_profile(args.save_profile)
            logging.info(f"Profile saved: {args.save_profile}")
        except Exception as e:
            logging.error(f"Error saving profile: {e}")
            return 1
    
    # Initialize scraper
    try:
        scraper = EnhancedTwitterScraper(config)
        
        # Handle streaming mode
        if args.stream:
            # Stream tweets
            def process_tweet(tweet):
                tweet_id = tweet.get('id_str')
                text = tweet.get('full_text', '')[:80]
                if len(tweet.get('full_text', '')) > 80:
                    text += '...'
                print(f"[{tweet_id}] {text}")
                return True  # Continue streaming
            
            print(f"Streaming tweets for query: {args.query or f'@{config.username}'}")
            print("Press Ctrl+C to stop...")
            
            scraper.stream_tweets(callback=process_tweet, query=args.query)
            return 0
            
        # Handle multi-query mode
        if args.queries_file:
            queries = []
            try:
                with open(args.queries_file, 'r', encoding='utf-8') as f:
                    queries = [line.strip() for line in f if line.strip()]
            except Exception as e:
                logging.error(f"Error reading queries file: {e}")
                return 1
                
            if not queries:
                logging.error("No queries found in the specified file")
                return 1
                
            print(f"Running {len(queries)} queries...")
            results = scraper.fetch_multiple_queries(queries)
            
            all_tweets = []
            for query, tweets in results.items():
                print(f"Query '{query}': {len(tweets)} tweets")
                all_tweets.extend(tweets)
                
            # Remove duplicates
            seen_ids = set()
            unique_tweets = []
            for tweet in all_tweets:
                tweet_id = tweet.get('id_str')
                if tweet_id and tweet_id not in seen_ids:
                    seen_ids.add(tweet_id)
                    unique_tweets.append(tweet)
            
            print(f"Total unique tweets across all queries: {len(unique_tweets)}")
            
            # Save tweets
            if unique_tweets:
                for fmt in config.export_formats:
                    filename = scraper.save_tweets(unique_tweets, format=fmt)
                    print(f"Saved to {filename}")
                
                # Analyze if requested
                if args.analyze:
                    print_analysis(scraper.analyze_tweets(unique_tweets))
            
            return 0
            
        # Regular single query/username mode
        query = args.query
        if not query and config.username:
            # Verify account
            print(f"Verifying account: @{config.username}")
            account_info = scraper.verify_account()
            
            if not account_info['success']:
                logging.error(f"Could not verify account: {account_info.get('error')}")
                return 1
                
            print(f"Account verified: {account_info['name']}")
            print(f"Total tweets: {account_info['total_tweets']:,}")
            print(f"Followers: {account_info['followers']:,}")
            
            if account_info['protected']:
                logging.error("This account is protected. Cannot fetch tweets.")
                return 1
                
            # Use default query based on username and scrape type
            query = None  # Let fetch_tweets construct the query
        
        # Collect tweets
        print(f"Collecting tweets{f' for query: {query}' if query else ''}...")
        tweets = scraper.fetch_tweets_for_query(query) if query else scraper.fetch_tweets()
        
        if tweets:
            print(f"Collected {len(tweets)} tweets")
            
            # Save tweets in all requested formats
            for fmt in config.export_formats:
                filename = scraper.save_tweets(tweets, format=fmt)
                print(f"Saved to {filename}")
            
            # Analyze if requested
            if args.analyze:
                print_analysis(scraper.analyze_tweets(tweets))
        else:
            print("No tweets collected")
                
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        logging.error(f"Error: {e}")
        return 1
    
    return 0

def print_analysis(analysis):
    """Pretty print tweet analysis results"""
    print("\n===== TWEET ANALYSIS =====")
    print(f"Total tweets: {analysis['tweet_count']}")
    
    # Engagement stats
    print("\n----- Engagement Stats -----")
    print(f"Total likes: {analysis['engagement']['total_likes']:,}")
    print(f"Total retweets: {analysis['engagement']['total_retweets']:,}")
    print(f"Total replies: {analysis['engagement']['total_replies']:,}")
    print(f"Average likes per tweet: {analysis['engagement']['average_likes']:.1f}")
    print(f"Average retweets per tweet: {analysis['engagement']['average_retweets']:.1f}")
    
    # Top tweets
    print("\n----- Top Liked Tweets -----")
    for i, tweet in enumerate(analysis['top_liked_tweets']):
        print(f"{i+1}. [{tweet['id']}] {tweet['text']} ({tweet['likes']:,} likes)")
    
    print("\n----- Top Retweeted Tweets -----")
    for i, tweet in enumerate(analysis['top_retweeted_tweets']):
        print(f"{i+1}. [{tweet['id']}] {tweet['text']} ({tweet['retweets']:,} retweets)")
    
    # Hashtags
    if analysis['hashtag_analysis']['top_hashtags']:
        print("\n----- Top Hashtags -----")
        for tag, count in analysis['hashtag_analysis']['top_hashtags']:
            print(f"#{tag}: {count} uses")
    
    # Mentions
    if analysis['mention_analysis']['top_mentions']:
        print("\n----- Top Mentions -----")
        for user, count in analysis['mention_analysis']['top_mentions']:
            print(f"@{user}: {count} mentions")
    
    # Domains
    if analysis['url_analysis']['top_domains']:
        print("\n----- Top Domains -----")
        for domain, count in analysis['url_analysis']['top_domains']:
            print(f"{domain}: {count} links")
    
    # Time analysis
    print("\n----- Activity by Hour -----")
    hours = sorted(analysis['time_analysis']['hour_activity'].items())
    for hour, count in hours:
        print(f"{hour:02d}:00 - {hour:02d}:59: {count} tweets")
    
    print("\n----- Activity by Day -----")
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_data = analysis['time_analysis']['day_activity']
    for day in days_order:
        if day in day_data:
            print(f"{day}: {day_data[day]} tweets")

if __name__ == "__main__":
    sys.exit(main())