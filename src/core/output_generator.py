"""
Output Generator - Module for generating output in different formats
"""

import csv
import json
import logging
import xml.dom.minidom
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

class OutputGenerator:
    """Class for generating output in different formats (CSV, XML)"""
    
    def __init__(self, output_dir: str = "output"):
        """
        Initialize the output generator
        
        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def create_output_folder(self, username: str) -> Path:
        """
        Create a timestamped output folder for a specific username
        
        Args:
            username: Twitter username
            
        Returns:
            Path object for the output folder
        """
        # Create a timestamped folder name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder_name = f"{username}_{timestamp}"
        folder_path = self.output_dir / folder_name
        
        # Create the folder
        folder_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Created output folder: {folder_path}")
        
        return folder_path
    
    def save_tweets_to_csv(self, tweets: List[Dict], folder_path: Path, simple: bool = False) -> str:
        """
        Save tweets to CSV file
        
        Args:
            tweets: List of tweet objects
            folder_path: Path to the output folder
            simple: Whether to save only basic tweet data (text and timestamp)
            
        Returns:
            Path to the saved file
        """
        if not tweets:
            self.logger.warning("No tweets to save")
            return ""
        
        # Determine the filename based on simple flag
        if simple:
            filename = folder_path / "tweets_simple.csv"
            fieldnames = ['tweet_id', 'created_at', 'text']
        else:
            filename = folder_path / "tweets_full.csv"
            fieldnames = [
                'tweet_id', 'created_at', 'text', 'author', 'author_name',
                'retweets', 'likes', 'replies', 'is_reply', 'is_retweet',
                'topics', 'sentiment', 'style'
            ]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for tweet in tweets:
                    if simple:
                        row = {
                            'tweet_id': tweet.get('tweet_id', ''),
                            'created_at': tweet.get('created_at', ''),
                            'text': tweet.get('text', '')
                        }
                    else:
                        # Format the tags into strings
                        topics = ', '.join(tweet.get('tags', {}).get('topics', []))
                        sentiment = tweet.get('tags', {}).get('sentiment', 'neutral')
                        style = ', '.join(tweet.get('tags', {}).get('style', ['standard']))
                        
                        row = {
                            'tweet_id': tweet.get('tweet_id', ''),
                            'created_at': tweet.get('created_at', ''),
                            'text': tweet.get('text', ''),
                            'author': tweet.get('author', ''),
                            'author_name': tweet.get('author_name', ''),
                            'retweets': tweet.get('retweets', 0),
                            'likes': tweet.get('likes', 0),
                            'replies': tweet.get('replies', 0),
                            'is_reply': tweet.get('is_reply', False),
                            'is_retweet': tweet.get('is_retweet', False),
                            'topics': topics,
                            'sentiment': sentiment,
                            'style': style
                        }
                    
                    writer.writerow(row)
            
            self.logger.info(f"Saved {len(tweets)} tweets to {filename}")
            return str(filename)
        
        except Exception as e:
            self.logger.error(f"Error saving tweets to CSV: {e}")
            return ""
    
    def save_tweets_to_xml(self, tweets: List[Dict], folder_path: Path, account_info: Dict = None) -> str:
        """
        Save tweets to XML file with tags
        
        Args:
            tweets: List of tweet objects
            folder_path: Path to the output folder
            account_info: Optional dictionary with account information
            
        Returns:
            Path to the saved file
        """
        if not tweets:
            self.logger.warning("No tweets to save")
            return ""
        
        try:
            # Create the root element
            root = ET.Element("TwitterData")
            
            # Add metadata
            metadata = ET.SubElement(root, "Metadata")
            ET.SubElement(metadata, "ExportDate").text = datetime.now().isoformat()
            
            # Add account info if provided
            if account_info:
                account = ET.SubElement(root, "Account")
                ET.SubElement(account, "Username").text = account_info.get('screen_name', '')
                ET.SubElement(account, "Name").text = account_info.get('name', '')
                ET.SubElement(account, "FollowersCount").text = str(account_info.get('followers_count', 0))
                ET.SubElement(account, "FriendsCount").text = str(account_info.get('friends_count', 0))
                ET.SubElement(account, "StatusesCount").text = str(account_info.get('statuses_count', 0))
                ET.SubElement(account, "CreatedAt").text = str(account_info.get('created_at', ''))
            
            # Extract all unique topics, styles, etc. for tag reference
            all_topics = set()
            all_styles = set()
            
            for tweet in tweets:
                tags = tweet.get('tags', {})
                all_topics.update(tags.get('topics', []))
                all_styles.update(tags.get('style', []))
            
            # Add tag reference
            tag_reference = ET.SubElement(root, "TagReference")
            
            topics_ref = ET.SubElement(tag_reference, "Topics")
            for topic in sorted(all_topics):
                ET.SubElement(topics_ref, "Topic").text = topic
            
            styles_ref = ET.SubElement(tag_reference, "Styles")
            for style in sorted(all_styles):
                ET.SubElement(styles_ref, "Style").text = style
            
            # Add tweets
            tweets_element = ET.SubElement(root, "Tweets")
            
            for tweet in tweets:
                tweet_element = ET.SubElement(tweets_element, "Tweet")
                ET.SubElement(tweet_element, "ID").text = tweet.get('tweet_id', '')
                ET.SubElement(tweet_element, "CreatedAt").text = tweet.get('created_at', '')
                ET.SubElement(tweet_element, "Text").text = tweet.get('text', '')
                ET.SubElement(tweet_element, "Author").text = tweet.get('author', '')
                ET.SubElement(tweet_element, "Retweets").text = str(tweet.get('retweets', 0))
                ET.SubElement(tweet_element, "Likes").text = str(tweet.get('likes', 0))
                ET.SubElement(tweet_element, "Replies").text = str(tweet.get('replies', 0))
                ET.SubElement(tweet_element, "IsReply").text = str(tweet.get('is_reply', False)).lower()
                ET.SubElement(tweet_element, "IsRetweet").text = str(tweet.get('is_retweet', False)).lower()
                
                # Add tags
                tags = tweet.get('tags', {})
                tags_element = ET.SubElement(tweet_element, "Tags")
                
                # Add topic tags
                topics_element = ET.SubElement(tags_element, "Topics")
                for topic in tags.get('topics', []):
                    ET.SubElement(topics_element, "Topic").text = topic
                
                # Add sentiment
                ET.SubElement(tags_element, "Sentiment").text = tags.get('sentiment', 'neutral')
                
                # Add style tags
                styles_element = ET.SubElement(tags_element, "Styles")
                for style in tags.get('style', ['standard']):
                    ET.SubElement(styles_element, "Style").text = style
            
            # Create pretty XML
            xml_string = ET.tostring(root, encoding='utf-8')
            pretty_xml = xml.dom.minidom.parseString(xml_string).toprettyxml(indent="  ")
            
            # Save to file
            filename = folder_path / "tweets.xml"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            
            self.logger.info(f"Saved {len(tweets)} tweets to XML file: {filename}")
            return str(filename)
        
        except Exception as e:
            self.logger.error(f"Error saving tweets to XML: {e}")
            return ""
    
    def save_account_info(self, account_info: Dict, folder_path: Path) -> str:
        """
        Save account information to JSON file
        
        Args:
            account_info: Dictionary with account information
            folder_path: Path to the output folder
            
        Returns:
            Path to the saved file
        """
        if not account_info:
            self.logger.warning("No account info to save")
            return ""
        
        try:
            # Save to file
            filename = folder_path / "account_info.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(account_info, f, indent=2)
            
            self.logger.info(f"Saved account info to {filename}")
            return str(filename)
        
        except Exception as e:
            self.logger.error(f"Error saving account info: {e}")
            return ""