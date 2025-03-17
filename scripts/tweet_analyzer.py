#!/usr/bin/env python3
"""
Tweet Analyzer - Main script for fetching, processing, and saving tweets
"""
import argparse
import logging
import sys
import os
import json  # Add this import for saving JSON data
from datetime import datetime
from pathlib import Path

# Add the project root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.socialdata_client import SocialDataClient
from src.core.tweet_fetcher import TweetFetcher
from src.core.tweet_processor import TweetProcessor
from src.core.output_generator import OutputGenerator
from src.core.language_analyzer_light import LightweightLanguageAnalyzer

def setup_logging(level=logging.INFO):
    """Set up logging configuration"""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.FileHandler('tweet_analyzer.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def parse_date(date_str: str):
    """Parse date string in YYYY-MM-DD format"""
    if not date_str:
        return None
    
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        logging.error(f"Invalid date format: {date_str}. Please use YYYY-MM-DD")
        return None

def main():
    """Main function"""
    # Set up command line arguments
    parser = argparse.ArgumentParser(description='Fetch and analyze tweets')
    
    parser.add_argument('username', help='Twitter username (without @)')
    parser.add_argument('--type', choices=['tweets', 'replies', 'both'], default='both',
                      help='Type of tweets to fetch (default: both)')
    parser.add_argument('--max', type=int, default=1000,
                      help='Maximum number of tweets to fetch (default: 1000)')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--output-dir', default='output',
                      help='Directory for output files (default: output)')
    parser.add_argument('--verbose', action='store_true',
                      help='Enable verbose logging')
    parser.add_argument('--skip-advanced', action='store_true',
                    help='Skip advanced language analysis (faster, but less insightful)')
    
    args = parser.parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logger = setup_logging(log_level)
    
    # Parse dates
    start_date = parse_date(args.start_date)
    end_date = parse_date(args.end_date)
    
    # Initialize components
    client = SocialDataClient()
    fetcher = TweetFetcher(client)
    processor = TweetProcessor()
    output_gen = OutputGenerator(args.output_dir)
    
    try:
        # Step 1: Fetch account info
        logger.info(f"Fetching account info for @{args.username}")
        account_info = fetcher.fetch_user_info(args.username)
        logger.info(f"Account: {account_info['name']} (@{account_info['screen_name']})")
        logger.info(f"Followers: {account_info['followers_count']:,}, Following: {account_info['friends_count']:,}")
        logger.info(f"Tweets: {account_info['statuses_count']:,}")
        
        # Step 2: Create output folder
        output_folder = output_gen.create_output_folder(args.username)
        
        # Step 3: Save account info
        output_gen.save_account_info(account_info, output_folder)
        
        # Step 4: Fetch tweets
        logger.info(f"Fetching tweets for @{args.username}")
        tweets = fetcher.fetch_user_tweets(
            args.username,
            tweet_type=args.type,
            max_tweets=args.max,
            start_date=start_date,
            end_date=end_date
        )
        logger.info(f"Fetched {len(tweets)} tweets")
        
        # Step 5: Process tweets
        logger.info("Processing tweets...")
        processed_tweets = processor.process_tweets(tweets)
        
        # Step 6: Extract topics
        logger.info("Extracting topics...")
        topics = processor.extract_topics(processed_tweets)
        logger.info(f"Found {len(topics)} topics: {', '.join(topics)}")
        
        # Step 7: Tag tweets
        logger.info("Tagging tweets...")
        tagged_tweets = processor.tag_tweets(processed_tweets, topics)
        
        # Step 7.5: Perform lightweight language analysis (new)
        if not args.skip_advanced:
            logger.info("Performing advanced language analysis...")
            analyzer = LightweightLanguageAnalyzer()
            advanced_analysis = analyzer.analyze(tagged_tweets)
            
            # Save advanced analysis as JSON for reference
            advanced_json = output_folder / "advanced_analysis.json"
            with open(advanced_json, 'w', encoding='utf-8') as f:
                json.dump(advanced_analysis, f, indent=2)
            logger.info(f"Saved advanced analysis to {advanced_json}")

        # Step 8: Save to different formats
        logger.info("Saving tweets...")
        
        # Step 8.1: Save simple CSV (just text and timestamp)
        output_gen.save_tweets_to_csv(tagged_tweets, output_folder, simple=True)
        
        # Step 8.2: Save enhanced CSV with analysis
        output_gen.save_tweets_to_csv(tagged_tweets, output_folder, simple=False)
        
        # Step 8.3: Save lean XML with style analysis
        xml_file = output_gen.save_tweets_to_xml(tagged_tweets, output_folder, account_info)
        
        # Step 8.4: Generate human-readable summary text
        summary_file = output_gen.save_summary_text(tagged_tweets, output_folder, account_info)
        
        logger.info(f"All done! Output saved to: {output_folder}")
        
        # Print a summary of the files generated
        print(f"\nFiles generated:")
        print(f"- CSV (simple): {output_folder / 'tweets_simple.csv'}")
        print(f"- CSV (analysis): {output_folder / 'tweets_analysis.csv'}")  
        print(f"- XML: {output_folder / 'tweets_lean.xml'}")
        print(f"- Summary: {output_folder / 'account_summary.txt'}")
        print(f"- Account info: {output_folder / 'account_info.json'}")
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())