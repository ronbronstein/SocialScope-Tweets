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
from collections import Counter

from .language_analyzer_light import LightweightLanguageAnalyzer

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
        Generate a rich human-readable summary text file with advanced language analysis
        
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
            # Use the new lightweight language analyzer
            analyzer = LightweightLanguageAnalyzer()
            advanced_analysis = analyzer.analyze(tweets)
            
            # Prepare summary text
            summary_lines = []
            
            # Add header
            summary_lines.append("# TWITTER ACCOUNT ANALYSIS SUMMARY")
            summary_lines.append("=" * 80)
            
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
            
            # Add writing style analysis
            if "writing_style" in advanced_analysis:
                style = advanced_analysis["writing_style"]
                summary_lines.append(f"\n## WRITING STYLE ANALYSIS")
                
                # Voice and formality
                if "voice" in style and "formality" in style:
                    voice = style["voice"]
                    formality = style["formality"]
                    
                    summary_lines.append("\n### Voice and Tone")
                    summary_lines.append(f"Dominant voice: {voice.get('dominant_voice', 'Neutral')}")
                    
                    # Add voice breakdown
                    summary_lines.append(f"- First person (I, we, me): {voice.get('first_person_ratio', 0)*100:.1f}%")
                    summary_lines.append(f"- Second person (you, your): {voice.get('second_person_ratio', 0)*100:.1f}%")
                    summary_lines.append(f"- Third person (he, she, they): {voice.get('third_person_ratio', 0)*100:.1f}%")
                    
                    # Add formality
                    summary_lines.append(f"\nFormality level: {formality.get('level', 'Neutral')}")
                    summary_lines.append(f"- Formal markers: {formality.get('formal_markers', 0)} instances")
                    summary_lines.append(f"- Informal markers: {formality.get('informal_markers', 0)} instances")
                
                # Sentence complexity
                if "sentence_structure" in style:
                    structure = style["sentence_structure"]
                    summary_lines.append("\n### Sentence Structure")
                    summary_lines.append(f"Average sentence length: {structure.get('avg_sentence_length', 0):.1f} words")
                    
                    # Add question and exclamation stats
                    summary_lines.append(f"Question sentences: {structure.get('question_ratio', 0)*100:.1f}% of total")
                    summary_lines.append(f"Exclamatory sentences: {structure.get('exclamation_ratio', 0)*100:.1f}% of total")
                
                # Vocabulary richness
                if "vocabulary" in style:
                    vocabulary = style["vocabulary"]
                    summary_lines.append("\n### Vocabulary")
                    summary_lines.append(f"Vocabulary richness: {vocabulary.get('richness', 0):.3f}")
                    summary_lines.append("(Higher values indicate more diverse vocabulary)")
                    
                    # Add top words
                    if "top_words" in vocabulary:
                        summary_lines.append("\nMost frequent significant words:")
                        for word_data in vocabulary["top_words"][:10]:
                            summary_lines.append(f"- {word_data['word']}: {word_data['count']} times")
                    
                    # Add top phrases
                    if "top_phrases" in vocabulary:
                        summary_lines.append("\nCharacteristic phrases:")
                        for phrase_data in vocabulary["top_phrases"]:
                            summary_lines.append(f"- \"{phrase_data['phrase']}\": {phrase_data['count']} times")
            
            # Add readability analysis
            if "readability" in advanced_analysis:
                readability = advanced_analysis["readability"]
                summary_lines.append(f"\n## READABILITY ANALYSIS")
                
                if "scores" in readability:
                    scores = readability["scores"]
                    summary_lines.append(f"Flesch Reading Ease: {scores.get('flesch_reading_ease', 0):.1f}/100")
                    summary_lines.append(f"Flesch-Kincaid Grade Level: {scores.get('flesch_kincaid_grade', 0):.1f}")
                    
                    # Add interpretation
                    summary_lines.append(f"\nInterpretation: {readability.get('interpretation', 'N/A')}")
                    
                    # Add Twitter optimization insight
                    is_optimal = readability.get('is_optimal_for_social', False)
                    if is_optimal:
                        summary_lines.append("\nThis readability level is optimal for Twitter/social media.")
                    else:
                        summary_lines.append("\nThis readability level may not be optimal for Twitter/social media.")
                    
                    # Add words per tweet
                    summary_lines.append(f"\nAverage words per tweet: {readability.get('avg_words_per_tweet', 0):.1f}")
                    
                    # Add readability insights
                    if "insights" in readability:
                        summary_lines.append("\nReadability insights:")
                        for insight in readability["insights"]:
                            summary_lines.append(f"- {insight}")
            
            # Add temporal analysis if available
            if "temporal" in advanced_analysis:
                temporal = advanced_analysis["temporal"]
                
                if temporal.get("evolution_insights"):
                    summary_lines.append(f"\n## WRITING EVOLUTION OVER TIME")
                    summary_lines.append(f"Analysis period: {temporal.get('start_date', 'Unknown')} to {temporal.get('end_date', 'Unknown')}")
                    summary_lines.append(f"Time segmentation: {temporal.get('period_type', 'Unknown')}")
                    
                    # Add key insights
                    summary_lines.append("\nKey trends:")
                    for insight in temporal.get("evolution_insights", []):
                        summary_lines.append(f"- {insight}")
                    
                    # Add trend metrics
                    if "trends" in temporal:
                        trends = temporal["trends"]
                        metrics_to_show = [
                            ('sentiment', 'Sentiment'), 
                            ('readability', 'Readability'),
                            ('avg_engagement', 'Engagement')
                        ]
                        
                        summary_lines.append("\nDetailed Trends:")
                        for metric_key, metric_name in metrics_to_show:
                            if f"{metric_key}_trend" in trends:
                                trend = trends[f"{metric_key}_trend"]
                                change = trends.get(f"{metric_key}_change_pct", 0)
                                summary_lines.append(f"- {metric_name}: {trend} ({change:+.1f}%)")
            
            # Add engagement analysis
            if "engagement" in advanced_analysis:
                engagement = advanced_analysis["engagement"]
                
                if "engagement_insights" in engagement and engagement["engagement_insights"]:
                    summary_lines.append(f"\n## ENGAGEMENT PATTERNS")
                    
                    # Add key insights
                    summary_lines.append("What drives higher engagement:")
                    for insight in engagement.get("engagement_insights", []):
                        summary_lines.append(f"- {insight}")
                    
                    # Add high vs low comparison highlights
                    if "high_vs_low_comparison" in engagement:
                        comparison = engagement["high_vs_low_comparison"]
                        
                        summary_lines.append("\nHigh vs. Low Engagement Content Comparison:")
                        
                        # Readability comparison
                        if "readability" in comparison:
                            read_comp = comparison["readability"]
                            diff = read_comp.get("difference", 0)
                            if abs(diff) > 5:
                                if diff > 0:
                                    summary_lines.append("- High-engagement content is more readable")
                                else:
                                    summary_lines.append("- High-engagement content is more complex")
                        
                        # Sentiment comparison
                        if "sentiment" in comparison:
                            sent_comp = comparison["sentiment"]
                            diff = sent_comp.get("difference", 0)
                            if abs(diff) > 0.2:
                                if diff > 0:
                                    summary_lines.append("- High-engagement content is more positive")
                                else:
                                    summary_lines.append("- High-engagement content is more critical/negative")
                        
                        # Length comparison
                        if "avg_length" in comparison:
                            len_comp = comparison["avg_length"]
                            diff = len_comp.get("difference", 0)
                            if abs(diff) > 3:
                                if diff > 0:
                                    summary_lines.append(f"- High-engagement tweets are longer (by {diff:.1f} words)")
                                else:
                                    summary_lines.append(f"- High-engagement tweets are shorter (by {abs(diff):.1f} words)")
                    
                    # Add top tweets
                    if "top_engaging_tweets" in engagement and engagement["top_engaging_tweets"]:
                        top_tweets = engagement["top_engaging_tweets"]
                        summary_lines.append("\nMost engaging tweet examples:")
                        for i, tweet in enumerate(top_tweets[:3], 1):
                            summary_lines.append(f"{i}. \"{tweet.get('text', '')}\"")
                            summary_lines.append(f"   Engagement: {tweet.get('engagement', 0)}")
            
            # Add persuasive language analysis
            if "persuasive_patterns" in advanced_analysis:
                persuasive = advanced_analysis["persuasive_patterns"]
                
                summary_lines.append(f"\n## PERSUASIVE LANGUAGE PATTERNS")
                
                # Add persuasive style
                if "dominant_style" in persuasive:
                    summary_lines.append(f"Dominant persuasive style: {persuasive.get('dominant_style', 'Mixed')}")
                
                # Add top persuasive markers
                if "top_markers" in persuasive:
                    markers = persuasive["top_markers"]
                    if markers:
                        summary_lines.append("\nTop persuasive markers:")
                        for marker, count in markers.items():
                            summary_lines.append(f"- '{marker}': {count} instances")
                
                # Add other persuasive elements
                summary_lines.append(f"\nRhetorical questions: {persuasive.get('rhetorical_questions', 0)} instances")
                summary_lines.append(f"Call-to-action elements: {persuasive.get('calls_to_action', 0)} instances")
                summary_lines.append(f"Social proof references: {persuasive.get('social_proof_markers', 0)} instances")
                
                # Add persuasive insights
                if "insights" in persuasive:
                    summary_lines.append("\nPersuasive style insights:")
                    for insight in persuasive["insights"]:
                        summary_lines.append(f"- {insight}")
            
            # Add practical insights
            if "practical_insights" in advanced_analysis:
                practical = advanced_analysis["practical_insights"]
                
                summary_lines.append(f"\n## WRITING RECOMMENDATIONS")
                
                # Add specific recommendations
                if "writing_recommendations" in practical:
                    recommendations = practical["writing_recommendations"]
                    summary_lines.append("To emulate this writing style effectively:")
                    for rec in recommendations:
                        summary_lines.append(f"- {rec}")
                
                # Add key vocabulary
                if "vocabulary_themes" in practical:
                    vocab = practical["vocabulary_themes"]
                    
                    # Add key nouns
                    if "key_nouns" in vocab and vocab["key_nouns"]:
                        summary_lines.append("\nCharacteristic nouns to incorporate:")
                        summary_lines.append(", ".join(item["word"] for item in vocab["key_nouns"][:8]))
                    
                    # Add key verbs
                    if "key_verbs" in vocab and vocab["key_verbs"]:
                        summary_lines.append("\nCharacteristic verbs to incorporate:")
                        summary_lines.append(", ".join(item["word"] for item in vocab["key_verbs"][:8]))
                    
                    # Add key adjectives
                    if "key_adjectives" in vocab and vocab["key_adjectives"]:
                        summary_lines.append("\nCharacteristic adjectives to incorporate:")
                        summary_lines.append(", ".join(item["word"] for item in vocab["key_adjectives"][:8]))
                
                # Add emoji usage if relevant
                if "emoji_usage" in practical and practical["emoji_usage"].get("uses_emoji"):
                    emoji_info = practical["emoji_usage"]
                    if emoji_info.get("top_emojis"):
                        summary_lines.append("\nCharacteristic emojis to incorporate:")
                        emojis = [item["emoji"] for item in emoji_info.get("top_emojis", [])]
                        summary_lines.append(" ".join(emojis[:10]))
            
            # Add footer
            summary_lines.append("\n" + "=" * 80)
            summary_lines.append("Generated by SocialScope-Tweets Advanced Language Analysis")
            summary_lines.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # Save to file
            filename = folder_path / "writing_style_analysis.txt"
            with open(filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(summary_lines))
            
            self.logger.info(f"Saved advanced writing style analysis to {filename}")
            return str(filename)
        
        except Exception as e:
            self.logger.error(f"Error saving advanced analysis: {e}")
            # Fall back to basic summary if advanced analysis fails
            return self._save_basic_summary(tweets, folder_path, account_info)