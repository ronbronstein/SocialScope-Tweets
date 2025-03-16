"""
Output Generator - Module for generating output in different formats
"""

import csv
import json
import logging
import xml.dom.minidom
import xml.etree.ElementTree as ET
import re
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
        Save tweets to CSV file with improved formatting for easier analysis
        
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
            filename = folder_path / "tweets_analysis.csv"
            fieldnames = [
                'tweet_id', 'created_at', 'text', 'engagement_score', 
                'sentiment', 'style', 'topics'  # Simplified fields
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
                        # Calculate engagement score (simplified metric)
                        engagement = tweet.get('likes', 0) + (tweet.get('retweets', 0) * 2) + (tweet.get('replies', 0) * 3)
                        
                        # Format the tags into strings
                        topics = ', '.join(tweet.get('tags', {}).get('topics', []))
                        sentiment = tweet.get('tags', {}).get('sentiment', 'neutral')
                        style = ', '.join(tweet.get('tags', {}).get('style', ['standard']))
                        
                        row = {
                            'tweet_id': tweet.get('tweet_id', ''),
                            'created_at': tweet.get('created_at', ''),
                            'text': tweet.get('text', ''),
                            'engagement_score': engagement,
                            'sentiment': sentiment,
                            'style': style,
                            'topics': topics
                        }
                    
                    writer.writerow(row)
            
            self.logger.info(f"Saved {len(tweets)} tweets to {filename}")
            return str(filename)
        
        except Exception as e:
            self.logger.error(f"Error saving tweets to CSV: {e}")
            return ""
    
    def _analyze_writing_style(self, tweets: List[Dict]) -> Dict:
        """
        Analyze writing style patterns across all tweets for AI training
        
        Args:
            tweets: List of tweet objects
            
        Returns:
            Dictionary with writing style metrics and patterns
        """
        if not tweets:
            return {}
        
        # Initialize analysis containers
        analysis = {
            "GeneralMetrics": {},
            "VocabularyMetrics": {},
            "SentimentDistribution": {},
            "StylePatterns": {},
            "CommonPhrases": [],
            "TypicalFormats": []
        }
        
        # Track various metrics
        total_tweets = len(tweets)
        total_chars = 0
        total_words = 0
        total_sentences = 0
        
        # Word frequency analysis
        word_freq = {}
        phrase_freq = {}
        
        # Style patterns
        styles_count = {}
        sentiment_count = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        # Sentence beginnings and endings
        sentence_starters = {}
        sentence_endings = {}
        
        # Punctuation usage
        punctuation_usage = {'!': 0, '?': 0, '.': 0, ',': 0, ':': 0, ';': 0, '-': 0, '...': 0}
        
        # Analyze each tweet
        for tweet in tweets:
            text = tweet.get('text', '')
            words = text.split()
            total_chars += len(text)
            total_words += len(words)
            
            # Identify sentences
            sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
            total_sentences += len(sentences)
            
            # Count words
            for word in words:
                word_lower = word.lower().strip('.,!?:;()-"\'')
                if len(word_lower) > 1:  # Skip single characters
                    word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
            
            # Count 2-word phrases
            if len(words) >= 2:
                for i in range(len(words) - 1):
                    phrase = f"{words[i].lower().strip('.,!?:;()-\"\'')}-{words[i+1].lower().strip('.,!?:;()-\"\'')}"
                    if len(phrase) > 3:  # Skip very short phrases
                        phrase_freq[phrase] = phrase_freq.get(phrase, 0) + 1
            
            # Sentence beginnings and endings
            for sentence in sentences:
                if sentence:
                    words = sentence.split()
                    if words:
                        # First word
                        first_word = words[0].lower().strip('.,!?:;()-"\'')
                        if len(first_word) > 1:
                            sentence_starters[first_word] = sentence_starters.get(first_word, 0) + 1
                        
                        # Last word
                        last_word = words[-1].lower().strip('.,!?:;()-"\'')
                        if len(last_word) > 1:
                            sentence_endings[last_word] = sentence_endings.get(last_word, 0) + 1
            
            # Count punctuation
            for char in text:
                if char in punctuation_usage:
                    punctuation_usage[char] += 1
            
            # Count "..." ellipsis
            punctuation_usage['...'] += text.count('...')
            
            # Count writing styles
            tags = tweet.get('tags', {})
            for style in tags.get('style', ['standard']):
                styles_count[style] = styles_count.get(style, 0) + 1
            
            # Count sentiment
            sentiment = tags.get('sentiment', 'neutral')
            sentiment_count[sentiment] += 1
        
        # Fill in analysis dict with processed data
        
        # General metrics
        if total_tweets > 0:
            analysis["GeneralMetrics"] = {
                "TweetCount": total_tweets,
                "AvgCharsPerTweet": round(total_chars / total_tweets, 1),
                "AvgWordsPerTweet": round(total_words / total_tweets, 1),
                "AvgSentencesPerTweet": round(total_sentences / total_tweets, 1),
                "ReplyPercentage": round(sum(1 for t in tweets if t.get('is_reply', False)) / total_tweets * 100, 1),
                "RetweetPercentage": round(sum(1 for t in tweets if t.get('is_retweet', False)) / total_tweets * 100, 1)
            }
        
        # Vocabulary metrics
        if word_freq:
            # Get unique words count
            unique_words = len(word_freq)
            
            # Sort words by frequency
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            
            # Top 20 words
            top_words = {word: count for word, count in sorted_words[:20]}
            
            analysis["VocabularyMetrics"] = {
                "UniqueWordCount": unique_words,
                "VocabularyDiversity": round(unique_words / total_words, 3) if total_words > 0 else 0,
                "MostFrequentWords": top_words
            }
        
        # Phrases
        if phrase_freq:
            sorted_phrases = sorted(phrase_freq.items(), key=lambda x: x[1], reverse=True)
            analysis["CommonPhrases"] = [phrase.replace('-', ' ') for phrase, _ in sorted_phrases[:15]]
        
        # Style patterns
        if styles_count:
            analysis["StylePatterns"] = {
                "WritingStyles": {style: round(count / total_tweets * 100, 1) for style, count in styles_count.items()},
                "SentenceStarters": dict(sorted(sentence_starters.items(), key=lambda x: x[1], reverse=True)[:10]),
                "SentenceEndings": dict(sorted(sentence_endings.items(), key=lambda x: x[1], reverse=True)[:10]),
                "PunctuationUsage": {char: round(count / total_chars * 100, 2) if total_chars > 0 else 0 
                                    for char, count in punctuation_usage.items() if count > 0}
            }
        
        # Sentiment distribution
        if sentiment_count:
            analysis["SentimentDistribution"] = {
                sentiment: round(count / total_tweets * 100, 1) for sentiment, count in sentiment_count.items()
            }
        
        # Identify typical formatting patterns
        format_patterns = []
        
        # Check for URL patterns
        url_percentage = sum(1 for t in tweets if 'http' in t.get('text', '')) / total_tweets if total_tweets > 0 else 0
        if url_percentage > 0.3:  # Over 30% of tweets have URLs
            format_patterns.append("Frequently includes URLs")
        
        # Check for mention patterns
        mention_percentage = sum(1 for t in tweets if '@' in t.get('text', '')) / total_tweets if total_tweets > 0 else 0
        if mention_percentage > 0.3:  # Over 30% of tweets have mentions
            format_patterns.append("Frequently includes @mentions")
        
        # Check for hashtag patterns
        hashtag_percentage = sum(1 for t in tweets if '#' in t.get('text', '')) / total_tweets if total_tweets > 0 else 0
        if hashtag_percentage > 0.3:  # Over 30% of tweets have hashtags
            format_patterns.append("Frequently uses hashtags")
        
        # Check for ALL CAPS usage
        caps_percentage = sum(1 for t in tweets if any(word.isupper() and len(word) > 1 for word in t.get('text', '').split())) / total_tweets if total_tweets > 0 else 0
        if caps_percentage > 0.2:  # Over 20% of tweets have capitalized words
            format_patterns.append("Emphasizes points with ALL CAPS")
        
        # Add to analysis
        analysis["TypicalFormats"] = format_patterns
        
        return analysis
    
    def save_tweets_to_xml(self, tweets: List[Dict], folder_path: Path, account_info: Dict = None) -> str:
        """
        Save tweets to a lean XML file optimized for AI analysis
        
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
            
            # Add metadata as attributes
            root.set("ExportDate", datetime.now().isoformat())
            
            # Add account info if provided
            if account_info:
                account = ET.SubElement(root, "Account")
                account.set("Username", account_info.get('screen_name', ''))
                account.set("Name", account_info.get('name', ''))
                account.set("FollowersCount", str(account_info.get('followers_count', 0)))
                account.set("FollowingCount", str(account_info.get('friends_count', 0)))
                account.set("TweetCount", str(account_info.get('statuses_count', 0)))
                account.set("CreatedAt", str(account_info.get('created_at', '')))
                
                # Add account description as element (since it can be longer)
                if account_info.get('description'):
                    desc = ET.SubElement(account, "Description")
                    desc.text = account_info.get('description', '')
            
            # Add writing style analysis
            style_analysis = self._analyze_writing_style(tweets)
            style = ET.SubElement(root, "StyleAnalysis")
            
            for category, values in style_analysis.items():
                cat_elem = ET.SubElement(style, category)
                
                # Handle different types of values
                if isinstance(values, dict):
                    for key, value in values.items():
                        item = ET.SubElement(cat_elem, "Item")
                        item.set("Name", str(key))
                        item.set("Value", str(value))
                elif isinstance(values, list):
                    for value in values:
                        item = ET.SubElement(cat_elem, "Item")
                        item.set("Value", str(value))
                else:
                    cat_elem.text = str(values)
            
            # Add tweets - much leaner format
            tweets_element = ET.SubElement(root, "Tweets")
            
            for tweet in tweets:
                tweet_element = ET.SubElement(tweets_element, "Tweet")
                tweet_element.set("ID", tweet.get('tweet_id', ''))
                tweet_element.set("CreatedAt", tweet.get('created_at', ''))
                tweet_element.set("Retweets", str(tweet.get('retweets', 0)))
                tweet_element.set("Likes", str(tweet.get('likes', 0)))
                tweet_element.set("Replies", str(tweet.get('replies', 0)))
                tweet_element.set("IsReply", str(tweet.get('is_reply', False)).lower())
                tweet_element.set("IsRetweet", str(tweet.get('is_retweet', False)).lower())
                
                # Add text as element (since it's important and can be long)
                ET.SubElement(tweet_element, "Text").text = tweet.get('text', '')
                
                # Add tags as attributes with comma separation
                tags = tweet.get('tags', {})
                tweet_element.set("Topics", ",".join(tags.get('topics', [])))
                tweet_element.set("Sentiment", tags.get('sentiment', 'neutral'))
                tweet_element.set("Style", ",".join(tags.get('style', ['standard'])))
            
            # Create XML with minimal formatting
            xml_string = ET.tostring(root, encoding='utf-8')
            
            # Use minidom for minimal formatting (just enough to be readable)
            dom = xml.dom.minidom.parseString(xml_string)
            pretty_xml = dom.toprettyxml(indent="  ")
            
            # Remove excessive empty lines that minidom creates
            pretty_xml = '\n'.join([line for line in pretty_xml.split('\n') if line.strip()])
            
            # Save to file
            filename = folder_path / "tweets_lean.xml"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
            
            self.logger.info(f"Saved {len(tweets)} tweets to lean XML file: {filename}")
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
    
    def save_summary_text(self, tweets: List[Dict], folder_path: Path, account_info: Dict = None) -> str:
        """
        Generate a simple human-readable summary text file
        
        Args:
            tweets: List of tweet objects
            folder_path: Path to the output folder
            account_info: Account information dictionary
            
        Returns:
            Path to the saved file
        """
        if not tweets:
            self.logger.warning("No tweets to summarize")
            return ""
        
        try:
            # Analyze writing style
            style_analysis = self._analyze_writing_style(tweets)
            
            # Prepare summary text
            summary_lines = []
            
            # Add header
            summary_lines.append("# TWITTER ACCOUNT ANALYSIS SUMMARY")
            summary_lines.append("=" * 50)
            
            # Add account info
            if account_info:
                summary_lines.append(f"\n## ACCOUNT: @{account_info.get('screen_name', 'Unknown')}")
                summary_lines.append(f"Name: {account_info.get('name', 'Unknown')}")
                summary_lines.append(f"Followers: {account_info.get('followers_count', 0):,}")
                summary_lines.append(f"Following: {account_info.get('friends_count', 0):,}")
                summary_lines.append(f"Total tweets: {account_info.get('statuses_count', 0):,}")
                summary_lines.append(f"Account created: {account_info.get('created_at', 'Unknown')}")
                if account_info.get('description'):
                    summary_lines.append(f"Bio: {account_info.get('description', '')}")
            
            # Add data collection info
            summary_lines.append(f"\n## DATA COLLECTION")
            summary_lines.append(f"Tweets analyzed: {len(tweets):,}")
            summary_lines.append(f"Analysis date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Add general metrics
            if "GeneralMetrics" in style_analysis:
                metrics = style_analysis["GeneralMetrics"]
                summary_lines.append(f"\n## GENERAL METRICS")
                summary_lines.append(f"Average tweet length: {metrics.get('AvgCharsPerTweet', 0)} characters")
                summary_lines.append(f"Average words per tweet: {metrics.get('AvgWordsPerTweet', 0)}")
                summary_lines.append(f"Replies percentage: {metrics.get('ReplyPercentage', 0)}%")
                summary_lines.append(f"Retweets percentage: {metrics.get('RetweetPercentage', 0)}%")
            
            # Add vocabulary metrics
            if "VocabularyMetrics" in style_analysis:
                vocab = style_analysis["VocabularyMetrics"]
                summary_lines.append(f"\n## VOCABULARY")
                summary_lines.append(f"Unique words: {vocab.get('UniqueWordCount', 0):,}")
                summary_lines.append(f"Vocabulary diversity: {vocab.get('VocabularyDiversity', 0):.3f}")
                
                # Most frequent words
                if "MostFrequentWords" in vocab:
                    summary_lines.append("\nMost frequent words:")
                    for word, count in list(vocab["MostFrequentWords"].items())[:10]:
                        summary_lines.append(f"- {word}: {count} times")
            
            # Add common phrases
            if "CommonPhrases" in style_analysis and style_analysis["CommonPhrases"]:
                summary_lines.append(f"\n## COMMON PHRASES")
                for phrase in style_analysis["CommonPhrases"][:10]:
                    summary_lines.append(f"- \"{phrase}\"")
            
            # Add sentiment distribution
            if "SentimentDistribution" in style_analysis:
                summary_lines.append(f"\n## SENTIMENT ANALYSIS")
                sentiment = style_analysis["SentimentDistribution"]
                summary_lines.append(f"Positive: {sentiment.get('positive', 0)}%")
                summary_lines.append(f"Neutral: {sentiment.get('neutral', 0)}%")
                summary_lines.append(f"Negative: {sentiment.get('negative', 0)}%")
            
            # Add style patterns
            if "StylePatterns" in style_analysis:
                styles = style_analysis["StylePatterns"]
                
                if "WritingStyles" in styles:
                    summary_lines.append(f"\n## WRITING STYLE")
                    for style, percentage in styles["WritingStyles"].items():
                        summary_lines.append(f"- {style.capitalize()}: {percentage}%")
            
            # Add typical formats
            if "TypicalFormats" in style_analysis and style_analysis["TypicalFormats"]:
                summary_lines.append(f"\n## TYPICAL FORMATTING")
                for format_pattern in style_analysis["TypicalFormats"]:
                    summary_lines.append(f"- {format_pattern}")
            
            # Add footer
            summary_lines.append("\n" + "=" * 50)
            summary_lines.append("Generated by SocialScope-Tweets")
            
            # Save to file
            filename = folder_path / "account_summary.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(summary_lines))
            
            self.logger.info(f"Saved account summary to {filename}")
            return str(filename)
        
        except Exception as e:
            self.logger.error(f"Error saving summary text: {e}")
            return ""