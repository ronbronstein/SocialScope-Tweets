"""
Tweet Processor - Module for processing and tagging tweets
"""

import re
import logging
from typing import Dict, List, Optional, Set, Any
from datetime import datetime
from collections import Counter
import string
from pathlib import Path

class TweetProcessor:
    """Class for processing and tagging tweets"""
    
    # Common stop words to exclude from topics extraction
    STOP_WORDS = {
        'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what', 
        'when', 'where', 'how', 'who', 'which', 'this', 'that', 'these', 'those', 
        'then', 'just', 'so', 'than', 'such', 'both', 'through', 'about', 'for',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'having', 'do', 'does', 'did', 'doing', 'to', 'from', 'in', 'out', 'on',
        'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there',
        'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
        'no', 'nor', 'not', 'only', 'own', 'same', 'too', 'very', 'can', 'will',
        'with', 'at', 'by', 'of', 'up', 'it', 'its', "it's", 'i', 'me', 'my', 'myself',
        'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
        'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she',
        "she's", 'her', 'hers', 'herself', 'they', 'them', 'their', 'theirs', 'themselves',
        'am', "i'm", "isn't", "aren't", "wasn't", "weren't", "hasn't", "haven't", "hadn't",
        "doesn't", "don't", "didn't", "shouldn't", "wouldn't", "couldn't", "can't", "won't",
        'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below',
        'while', 'why', 'how', 'could', 'should', 'would', 'may', 'might', 'must', 'now'
    }
    
    # Keywords for sentiment analysis
    POSITIVE_WORDS = {
        'good', 'great', 'awesome', 'excellent', 'wonderful', 'best', 'love', 'happy',
        'excited', 'nice', 'beautiful', 'perfect', 'amazing', 'fantastic', 'brilliant',
        'joy', 'celebrate', 'win', 'success', 'congratulations', 'delighted', 'proud',
        'optimistic', 'impressive', 'remarkable', 'exceptional', 'pleasure', 'grateful',
        'appreciate', 'thank', 'thanks', 'better', 'improved', 'impressive', 'positive',
        'hope', 'promising', 'praised', 'recommended', 'thrilled', 'enjoy', 'liked',
        'laugh', 'smile', 'fun', 'incredible', 'outstanding', 'superb', 'stunning',
        'magnificent', 'remarkable', 'delightful', 'favorable', 'encouraging'
    }
    
    NEGATIVE_WORDS = {
        'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'sad', 'angry',
        'upset', 'poor', 'disappointing', 'problem', 'fail', 'failure', 'mess',
        'trouble', 'unfortunately', 'sorry', 'disappointed', 'negative', 'unhappy',
        'worried', 'annoyed', 'frustrated', 'regret', 'mistake', 'difficult', 'issue',
        'concern', 'complaint', 'complain', 'afraid', 'terrible', 'horrific', 'dreadful',
        'unpleasant', 'unfavorable', 'inferior', 'lose', 'lost', 'worse', 'worst',
        'disaster', 'disgrace', 'fault', 'flaw', 'incorrect', 'ineffective', 'disadvantage',
        'dire', 'grim', 'severe', 'tragic', 'unsuccessful', 'ugly', 'undesirable'
    }
    
    # Words that indicate question style
    QUESTION_INDICATORS = {
        'what', 'who', 'where', 'when', 'why', 'how', 'which', 'whose', 'whom',
        'is', 'are', 'was', 'were', 'will', 'would', 'should', 'could', 'can',
        'may', 'might', 'must', 'do', 'does', 'did', 'has', 'have', 'had'
    }
    
    def __init__(self):
        """Initialize the tweet processor"""
        self.logger = logging.getLogger(__name__)
    
    def process_tweets(self, tweets: List[Dict]) -> List[Dict]:
        """
        Process tweets to extract clean text and add metadata
        
        Args:
            tweets: List of raw tweet objects
            
        Returns:
            List of processed tweet objects
        """
        processed_tweets = []
        
        for tweet in tweets:
            try:
                # Extract the full text and clean it
                text = tweet.get('full_text') or tweet.get('text', '')
                cleaned_text = self._clean_tweet_text(text)
                
                # Create a processed tweet object with the data we need
                processed_tweet = {
                    'tweet_id': tweet.get('id_str'),
                    'created_at': tweet.get('tweet_created_at') or tweet.get('created_at'),
                    'text': text,
                    'cleaned_text': cleaned_text,
                    'author': tweet.get('user', {}).get('screen_name'),
                    'author_name': tweet.get('user', {}).get('name'),
                    'retweets': tweet.get('retweet_count', 0),
                    'likes': tweet.get('favorite_count', 0),
                    'replies': tweet.get('reply_count', 0),
                    'is_reply': tweet.get('in_reply_to_status_id_str') is not None,
                    'is_retweet': tweet.get('retweeted_status') is not None,
                    # Keep the original data
                    'original_data': tweet
                }
                
                processed_tweets.append(processed_tweet)
            except Exception as e:
                self.logger.error(f"Error processing tweet: {e}")
                # Continue with next tweet
        
        self.logger.info(f"Processed {len(processed_tweets)} tweets")
        return processed_tweets
    
    def _clean_tweet_text(self, text: str) -> str:
        """
        Clean tweet text by removing URLs, mentions, hashtags, RT prefixes, etc.
        
        Args:
            text: Original tweet text
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove mentions (@username)
        text = re.sub(r'@\w+', '', text)
        
        # Remove hashtags (#topic)
        text = re.sub(r'#\w+', '', text)
        
        # Remove RT prefix
        text = re.sub(r'^RT\s+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_topics(self, tweets: List[Dict], min_count: int = 3, max_topics: int = 10) -> List[str]:
        """
        Extract common topics from a collection of tweets
        
        Args:
            tweets: List of processed tweet objects
            min_count: Minimum count for a topic to be included
            max_topics: Maximum number of topics to return
            
        Returns:
            List of topic strings
        """
        # Extract words from all tweets
        all_words = []
        for tweet in tweets:
            cleaned_text = tweet.get('cleaned_text', '')
            if not cleaned_text:
                continue
                
            # Tokenize into words
            words = cleaned_text.lower().split()
            
            # Filter out stop words, short words, etc.
            words = [word.strip(string.punctuation) for word in words]
            words = [word for word in words if word and len(word) > 2 and word not in self.STOP_WORDS]
            
            all_words.extend(words)
        
        # Count word frequencies
        word_counts = Counter(all_words)
        
        # Filter words by minimum count and get the top N topics
        topics = [word for word, count in word_counts.most_common(max_topics) if count >= min_count]
        
        self.logger.info(f"Extracted {len(topics)} topics: {', '.join(topics)}")
        return topics
    
    def analyze_sentiment(self, text: str) -> str:
        """
        Simple rule-based sentiment analysis
        
        Args:
            text: Tweet text
            
        Returns:
            Sentiment label ("positive", "negative", or "neutral")
        """
        if not text:
            return "neutral"
        
        # Convert to lowercase for case-insensitive matching
        text_lower = text.lower()
        
        # Count positive and negative words
        positive_count = sum(1 for word in self.POSITIVE_WORDS if word in text_lower)
        negative_count = sum(1 for word in self.NEGATIVE_WORDS if word in text_lower)
        
        # Determine sentiment based on counts
        if positive_count > negative_count:
            return "positive"
        elif negative_count > positive_count:
            return "negative"
        else:
            return "neutral"
    
    def analyze_writing_style(self, text: str) -> List[str]:
        """
        Analyze writing style of a tweet
        
        Args:
            text: Tweet text
            
        Returns:
            List of style labels
        """
        if not text:
            return ["standard"]
        
        styles = []
        
        # Check for questions
        if '?' in text:
            styles.append("question")
        elif any(word.lower() in self.QUESTION_INDICATORS for word in text.split()[:1]):
            # Check if first word is a question indicator
            styles.append("question")
        
        # Check for exclamations
        if '!' in text:
            styles.append("exclamatory")
        
        # Check for ALL CAPS (shouting)
        words = text.split()
        caps_words = sum(1 for word in words if word.isupper() and len(word) > 1)
        if caps_words > len(words) / 3:  # If more than 1/3 of words are ALL CAPS
            styles.append("emphatic")
        
        # Check for links/references
        if 'https://' in text or 'http://' in text:
            styles.append("reference")
        
        # Check for hashtags
        if '#' in text:
            styles.append("tagged")
        
        # Check for mentions
        if '@' in text:
            styles.append("conversational")
        
        # If no specific style detected, mark as standard
        if not styles:
            styles.append("standard")
        
        return styles
    
    def tag_tweets(self, tweets: List[Dict], topics: Optional[List[str]] = None) -> List[Dict]:
        """
        Add tags (topic, sentiment, writing style) to tweets
        
        Args:
            tweets: List of processed tweet objects
            topics: Optional list of pre-extracted topics
            
        Returns:
            List of tagged tweet objects
        """
        # Extract topics if not provided
        if topics is None:
            topics = self.extract_topics(tweets)
        
        tagged_tweets = []
        
        for tweet in tweets:
            text = tweet.get('cleaned_text', '')
            
            # Initialize tags
            tags = {
                'topics': [],
                'sentiment': self.analyze_sentiment(text),
                'style': self.analyze_writing_style(tweet.get('text', ''))
            }
            
            # Add topic tags
            for topic in topics:
                if topic.lower() in text.lower():
                    tags['topics'].append(topic)
            
            # Add tags to the tweet object
            tweet_with_tags = {**tweet, 'tags': tags}
            tagged_tweets.append(tweet_with_tags)
        
        self.logger.info(f"Tagged {len(tagged_tweets)} tweets")
        return tagged_tweets