"""
Lightweight Language Analyzer - Provides meaningful insights into writing style and patterns
without heavy dependencies
"""

import re
import logging
import json
from collections import Counter
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Set
import textstat

class LightweightLanguageAnalyzer:
    """
    Lightweight analysis of language patterns and writing style in tweet data.
    Focuses on meaningful insights without heavy NLP dependencies.
    """
    
    def __init__(self):
        """Initialize the language analyzer"""
        self.logger = logging.getLogger(__name__)
        
        # Lists of positive and negative sentiment words
        self.positive_words = {
            'good', 'great', 'awesome', 'excellent', 'wonderful', 'best', 'love', 'happy',
            'excited', 'nice', 'beautiful', 'perfect', 'amazing', 'fantastic', 'brilliant',
            'joy', 'celebrate', 'win', 'success', 'congratulations', 'delighted', 'proud',
            'optimistic', 'impressive', 'remarkable', 'exceptional', 'pleasure', 'grateful',
            'appreciate', 'thank', 'thanks', 'better', 'improved', 'positive', 'hope'
        }
        
        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'sad', 'angry',
            'upset', 'poor', 'disappointing', 'problem', 'fail', 'failure', 'mess',
            'trouble', 'unfortunately', 'sorry', 'disappointed', 'negative', 'unhappy',
            'worried', 'annoyed', 'frustrated', 'regret', 'mistake', 'difficult', 'issue'
        }
        
        # Common formal and informal words
        self.formal_words = {
            'therefore', 'thus', 'hence', 'accordingly', 'consequently', 'subsequently',
            'nevertheless', 'moreover', 'however', 'furthermore', 'additionally'
        }
        
        self.informal_words = {
            'yeah', 'nah', 'gonna', 'wanna', 'gotta', 'kinda', 'sorta', 'dunno',
            'lol', 'lmao', 'wow', 'cool', 'awesome', 'stuff', 'thing', 'like'
        }
        
        # First, second, and third person pronouns
        self.first_person = {'i', 'me', 'my', 'mine', 'myself', 'we', 'us', 'our', 'ours', 'ourselves'}
        self.second_person = {'you', 'your', 'yours', 'yourself', 'yourselves'}
        self.third_person = {
            'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself',
            'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves'
        }
        
        # Common stop words to ignore in analysis
        self.stop_words = {
            'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
            'when', 'where', 'how', 'who', 'which', 'this', 'that', 'these', 'those',
            'then', 'just', 'so', 'than', 'such', 'both', 'through', 'about', 'for',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'having', 'do', 'does', 'did', 'doing', 'to', 'from', 'in', 'out', 'on',
            'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there',
            'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
            'no', 'nor', 'not', 'only', 'own', 'same', 'too', 'very', 'can', 'will', 'with'
        }
        
        # Persuasive language patterns
        self.persuasive_markers = {
            'must': 'imperative',
            'need': 'imperative',
            'should': 'suggestive',
            'could': 'possibility',
            'might': 'possibility',
            'always': 'absolutism',
            'never': 'absolutism',
            'everyone': 'generalization',
            'nobody': 'generalization',
            'clearly': 'emphasis',
            'obviously': 'emphasis',
            'undoubtedly': 'emphasis',
            'imagine': 'visualization',
            'picture': 'visualization',
            'consider': 'engagement',
            'think about': 'engagement',
            'ask yourself': 'engagement',
            'remember': 'recall',
            'recall': 'recall'
        }
    
    def analyze(self, tweets: List[Dict]) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on tweet data
        
        Args:
            tweets: List of processed tweet objects with timestamps
            
        Returns:
            Dictionary containing multifaceted analysis results
        """
        if not tweets:
            self.logger.warning("No tweets to analyze")
            return {}
        
        # Sort tweets by date for temporal analysis
        sorted_tweets = sorted(tweets, key=lambda x: self._parse_date(x.get('created_at', '')))
        
        # Full analysis results
        analysis = {
            "writing_style": self._analyze_writing_style(sorted_tweets),
            "readability": self._analyze_readability(sorted_tweets),
            "temporal": self._analyze_temporal_patterns(sorted_tweets),
            "engagement": self._analyze_engagement_patterns(sorted_tweets),
            "persuasive_patterns": self._analyze_persuasive_patterns(sorted_tweets),
            "practical_insights": self._extract_practical_insights(sorted_tweets)
        }
        
        return analysis
    
    def _parse_date(self, date_str: str) -> datetime:
        """Parse tweet date string into datetime object"""
        if not date_str:
            return datetime.now()
        
        # Try various date formats
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',  # ISO format with microseconds and Z
            '%Y-%m-%dT%H:%M:%S%z',    # ISO format with timezone
            '%Y-%m-%dT%H:%M:%S.%f',   # ISO format with microseconds
            '%Y-%m-%dT%H:%M:%S',      # ISO format
            '%a %b %d %H:%M:%S %z %Y',  # Twitter format
            '%Y-%m-%d %H:%M:%S'       # Simple format
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # If all formats fail, use current date
        self.logger.warning(f"Could not parse date: {date_str}")
        return datetime.now()
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple word tokenization"""
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove mentions (@username)
        text = re.sub(r'@\w+', '', text)
        
        # Split into words, removing punctuation
        words = re.findall(r'\b\w+\b', text.lower())
        return words
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using basic rules"""
        # Try to split on ., !, ? but don't split decimal numbers
        text = re.sub(r'\.\.\.', '<ELLIPSIS>', text)  # Preserve ellipsis
        text = re.sub(r'([.!?])\s+', r'\1<SPLIT>', text)
        text = re.sub(r'<ELLIPSIS>', '...', text)
        
        sentences = [s.strip() for s in text.split('<SPLIT>') if s.strip()]
        return sentences
    
    def _analyze_writing_style(self, tweets: List[Dict]) -> Dict[str, Any]:
        """
        Analyze writing style patterns 
        """
        # Combine all tweet text
        all_text = " ".join(tweet.get('text', '') for tweet in tweets if tweet.get('text'))
        
        if not all_text:
            return {}
        
        # Tokenize words
        words = self._tokenize(all_text)
        total_words = len(words)
        
        # Calculate unique words (vocabulary richness)
        unique_words = len(set(words))
        vocabulary_richness = unique_words / total_words if total_words > 0 else 0
        
        # Split into sentences
        sentences = self._split_into_sentences(all_text)
        total_sentences = len(sentences)
        
        # Analyze sentences
        question_sentences = sum(1 for s in sentences if '?' in s)
        exclamation_sentences = sum(1 for s in sentences if '!' in s)
        
        # Calculate mean words per sentence
        words_per_sentence = [len(self._tokenize(s)) for s in sentences]
        avg_sentence_length = sum(words_per_sentence) / len(sentences) if sentences else 0
        
        # Analyze formality
        formal_count = sum(1 for word in words if word in self.formal_words)
        informal_count = sum(1 for word in words if word in self.informal_words)
        
        formality_ratio = formal_count / (formal_count + informal_count + 1)  # +1 to avoid division by zero
        
        if formality_ratio > 0.6:
            formality_level = "Formal"
        elif formality_ratio < 0.3:
            formality_level = "Informal"
        else:
            formality_level = "Neutral"
        
        # Analyze voice (1st, 2nd, 3rd person)
        first_person_count = sum(1 for word in words if word in self.first_person)
        second_person_count = sum(1 for word in words if word in self.second_person)
        third_person_count = sum(1 for word in words if word in self.third_person)
        
        total_person_refs = first_person_count + second_person_count + third_person_count
        if total_person_refs > 0:
            first_person_ratio = first_person_count / total_person_refs
            second_person_ratio = second_person_count / total_person_refs
            third_person_ratio = third_person_count / total_person_refs
        else:
            first_person_ratio = second_person_ratio = third_person_ratio = 0
        
        # Determine dominant voice
        dominant_voice = "Neutral"
        max_ratio = max(first_person_ratio, second_person_ratio, third_person_ratio)
        if max_ratio > 0.5:  # If one type is dominant
            if first_person_ratio == max_ratio:
                dominant_voice = "First Person"
            elif second_person_ratio == max_ratio:
                dominant_voice = "Second Person"
            else:
                dominant_voice = "Third Person"
        
        # Count most common words (excluding stop words)
        significant_words = [word for word in words if word not in self.stop_words and len(word) > 2]
        top_words = Counter(significant_words).most_common(15)
        
        # Find repeated patterns
        # Look for 2-3 word phrases that repeat
        text_lower = all_text.lower()
        bigrams = []
        for i in range(len(words) - 1):
            if words[i] not in self.stop_words and words[i+1] not in self.stop_words:
                bigram = f"{words[i]} {words[i+1]}"
                bigrams.append(bigram)
        
        top_bigrams = Counter(bigrams).most_common(5)
        
        return {
            "sentence_structure": {
                "avg_sentence_length": avg_sentence_length,
                "question_ratio": question_sentences / total_sentences if total_sentences > 0 else 0,
                "exclamation_ratio": exclamation_sentences / total_sentences if total_sentences > 0 else 0,
            },
            "vocabulary": {
                "richness": vocabulary_richness,
                "unique_words": unique_words,
                "total_words": total_words,
                "top_words": [{"word": word, "count": count} for word, count in top_words],
                "top_phrases": [{"phrase": phrase, "count": count} for phrase, count in top_bigrams]
            },
            "formality": {
                "score": formality_ratio,
                "level": formality_level,
                "formal_markers": formal_count,
                "informal_markers": informal_count
            },
            "voice": {
                "first_person_ratio": first_person_ratio,
                "second_person_ratio": second_person_ratio,
                "third_person_ratio": third_person_ratio,
                "dominant_voice": dominant_voice
            }
        }
    
    def _analyze_readability(self, tweets: List[Dict]) -> Dict[str, Any]:
        """
        Calculate readability metrics for the tweets
        """
        # Combine all tweets into one text for analysis
        all_text = " ".join(tweet.get('text', '') for tweet in tweets if tweet.get('text'))
        
        if not all_text:
            return {}
        
        # Calculate readability scores using textstat
        flesch_reading_ease = textstat.flesch_reading_ease(all_text)
        flesch_kincaid_grade = textstat.flesch_kincaid_grade(all_text)
        
        # Calculate average words per tweet
        words_per_tweet = [len(self._tokenize(tweet.get('text', ''))) 
                          for tweet in tweets if tweet.get('text')]
        avg_words_per_tweet = sum(words_per_tweet) / len(words_per_tweet) if words_per_tweet else 0
        
        # Interpret readability level
        if flesch_reading_ease >= 90:
            readability_interpretation = "Very Easy - 5th Grade"
        elif flesch_reading_ease >= 80:
            readability_interpretation = "Easy - 6th Grade"
        elif flesch_reading_ease >= 70:
            readability_interpretation = "Fairly Easy - 7th Grade"
        elif flesch_reading_ease >= 60:
            readability_interpretation = "Standard - 8th-9th Grade"
        elif flesch_reading_ease >= 50:
            readability_interpretation = "Fairly Difficult - 10th-12th Grade"
        elif flesch_reading_ease >= 30:
            readability_interpretation = "Difficult - College Level"
        else:
            readability_interpretation = "Very Difficult - College Graduate"
        
        # Check if readability is appropriate for Twitter
        is_optimal_for_twitter = 60 <= flesch_reading_ease <= 85
        
        # Readability insights
        readability_insights = []
        
        if flesch_reading_ease < 60:
            readability_insights.append("Content may be too complex for general social media audience")
        elif flesch_reading_ease > 85:
            readability_insights.append("Very accessible writing style suitable for broad audiences")
        else:
            readability_insights.append("Writing complexity is well-balanced for social media")
            
        if avg_words_per_tweet < 10:
            readability_insights.append("Very concise tweets, possibly too brief to convey complex ideas")
        elif avg_words_per_tweet > 25:
            readability_insights.append("Tweets are quite verbose, may lose reader engagement")
        else:
            readability_insights.append("Tweet length is well-optimized for engagement")
        
        return {
            "scores": {
                "flesch_reading_ease": flesch_reading_ease,
                "flesch_kincaid_grade": flesch_kincaid_grade,
            },
            "interpretation": readability_interpretation,
            "is_optimal_for_social": is_optimal_for_twitter,
            "avg_words_per_tweet": avg_words_per_tweet,
            "insights": readability_insights
        }
    
    def _analyze_sentiment(self, text: str) -> float:
        """
        Simple rule-based sentiment analysis
        Returns a score from -1 (negative) to 1 (positive)
        """
        words = self._tokenize(text)
        
        positive_count = sum(1 for word in words if word in self.positive_words)
        negative_count = sum(1 for word in words if word in self.negative_words)
        
        # Calculate normalized sentiment score
        total_words = len(words)
        if total_words > 0:
            sentiment_score = (positive_count - negative_count) / (total_words * 0.1)
            # Clamp to [-1, 1]
            sentiment_score = max(-1, min(1, sentiment_score))
        else:
            sentiment_score = 0
        
        return sentiment_score
    
    def _analyze_temporal_patterns(self, tweets: List[Dict]) -> Dict[str, Any]:
        """
        Analyze how language and style change over time
        """
        if not tweets or len(tweets) < 5:  # Need enough data for temporal analysis
            return {}
        
        # Group tweets by time periods
        start_date = self._parse_date(tweets[0].get('created_at', ''))
        end_date = self._parse_date(tweets[-1].get('created_at', ''))
        date_range = (end_date - start_date).days
        
        # Determine appropriate time segmentation based on date range
        if date_range <= 7:
            # Less than a week, use days
            period_type = "Daily"
            num_periods = min(date_range + 1, 7)  # Maximum 7 periods
        elif date_range <= 60:
            # Less than two months, use weeks
            period_type = "Weekly"
            num_periods = min(date_range // 7 + 1, 8)  # Maximum 8 periods
        else:
            # Longer periods, use months
            period_type = "Monthly"
            num_periods = min(date_range // 30 + 1, 12)  # Maximum 12 periods
        
        # Create equal-sized periods
        period_duration = date_range / num_periods if num_periods > 0 else 1
        
        periods = []
        for i in range(num_periods):
            period_start = start_date + timedelta(days=i * period_duration)
            period_end = start_date + timedelta(days=(i+1) * period_duration)
            
            # Find tweets in this period
            period_tweets = [t for t in tweets if 
                           period_start <= self._parse_date(t.get('created_at', '')) < period_end]
            
            # Skip empty periods
            if not period_tweets:
                continue
            
            # Calculate period metrics
            period_text = " ".join(t.get('text', '') for t in period_tweets)
            
            # Basic stats
            tweet_count = len(period_tweets)
            avg_engagement = sum((t.get('likes', 0) or 0) + 
                              (t.get('retweets', 0) or 0) + 
                              (t.get('replies', 0) or 0) for t in period_tweets) / tweet_count if tweet_count else 0
            
            # Sentiment
            avg_sentiment = sum(self._analyze_sentiment(t.get('text', '')) 
                              for t in period_tweets) / tweet_count if tweet_count else 0
            
            # Readability
            if period_text:
                readability = textstat.flesch_reading_ease(period_text)
            else:
                readability = 0
            
            # Add period data
            periods.append({
                'start_date': str(period_start.date()),
                'end_date': str(period_end.date()),
                'tweet_count': tweet_count,
                'avg_engagement': avg_engagement,
                'sentiment': avg_sentiment,
                'readability': readability
            })
        
        # Detect trends
        trends = {}
        
        # Only calculate trends if we have enough periods
        if len(periods) >= 3:
            # Calculate relative changes from first to last period
            first_period = periods[0]
            last_period = periods[-1]
            
            metrics = ['avg_engagement', 'sentiment', 'readability']
            
            for metric in metrics:
                if first_period[metric] != 0:
                    change_pct = ((last_period[metric] - first_period[metric]) / 
                                 abs(first_period[metric])) * 100
                    trends[f"{metric}_change_pct"] = change_pct
                    
                    # Interpret trend
                    if change_pct > 20:
                        trends[f"{metric}_trend"] = "Strong Increase"
                    elif change_pct > 5:
                        trends[f"{metric}_trend"] = "Slight Increase"
                    elif change_pct < -20:
                        trends[f"{metric}_trend"] = "Strong Decrease"
                    elif change_pct < -5:
                        trends[f"{metric}_trend"] = "Slight Decrease"
                    else:
                        trends[f"{metric}_trend"] = "Stable"
        
        # Generate writing evolution insights
        insights = []
        
        if 'sentiment_trend' in trends:
            if trends['sentiment_trend'] == "Strong Increase":
                insights.append("Voice has become significantly more positive over time")
            elif trends['sentiment_trend'] == "Strong Decrease":
                insights.append("Voice has become more negative or critical over time")
        
        if 'readability_trend' in trends:
            if trends['readability_trend'] in ["Strong Increase", "Slight Increase"]:
                insights.append("Writing has become easier to read over time")
            elif trends['readability_trend'] in ["Strong Decrease", "Slight Decrease"]:
                insights.append("Writing has become more complex over time")
        
        # Add engagement insights
        if 'avg_engagement_trend' in trends:
            if trends['avg_engagement_trend'] in ["Strong Increase", "Slight Increase"]:
                insights.append("Content is generating increasing engagement over time")
            elif trends['avg_engagement_trend'] in ["Strong Decrease", "Slight Decrease"]:
                insights.append("Content is generating less engagement over time")
        
        return {
            "period_type": period_type,
            "start_date": str(start_date.date()),
            "end_date": str(end_date.date()),
            "periods": periods,
            "trends": trends,
            "evolution_insights": insights
        }
    
    def _analyze_engagement_patterns(self, tweets: List[Dict]) -> Dict[str, Any]:
        """
        Analyze how language features correlate with engagement
        """
        if not tweets:
            return {}
        
        # Filter tweets with engagement metrics
        tweets_with_metrics = [t for t in tweets if 
                             any(t.get(metric, 0) for metric in ['likes', 'retweets', 'replies'])]
        
        if not tweets_with_metrics:
            return {}
        
        # Calculate total engagement for each tweet
        for tweet in tweets_with_metrics:
            tweet['total_engagement'] = (tweet.get('likes', 0) or 0) + \
                                      (tweet.get('retweets', 0) or 0) + \
                                      (tweet.get('replies', 0) or 0)
        
        # Sort by engagement
        sorted_tweets = sorted(tweets_with_metrics, key=lambda x: x.get('total_engagement', 0), reverse=True)
        
        # Separate high and low engagement tweets for comparison
        high_engagement_cutoff = max(len(sorted_tweets) // 3, 1)  # Top third, at least 1
        high_engagement_tweets = sorted_tweets[:high_engagement_cutoff]
        low_engagement_tweets = sorted_tweets[-high_engagement_cutoff:]  # Bottom third
        
        # Analyze both groups
        high_engagement_text = " ".join(t.get('text', '') for t in high_engagement_tweets)
        low_engagement_text = " ".join(t.get('text', '') for t in low_engagement_tweets)
        
        # Compare features
        
        # 1. Readability comparison
        if high_engagement_text and low_engagement_text:
            high_readability = textstat.flesch_reading_ease(high_engagement_text)
            low_readability = textstat.flesch_reading_ease(low_engagement_text)
            readability_diff = high_readability - low_readability
        else:
            high_readability = low_readability = readability_diff = 0
        
        # 2. Sentiment comparison
        high_sentiment = sum(self._analyze_sentiment(t.get('text', '')) 
                          for t in high_engagement_tweets) / len(high_engagement_tweets) if high_engagement_tweets else 0
        low_sentiment = sum(self._analyze_sentiment(t.get('text', '')) 
                         for t in low_engagement_tweets) / len(low_engagement_tweets) if low_engagement_tweets else 0
        sentiment_diff = high_sentiment - low_sentiment
        
        # 3. Length comparison
        high_length = sum(len(self._tokenize(t.get('text', ''))) for t in high_engagement_tweets) / len(high_engagement_tweets) if high_engagement_tweets else 0
        low_length = sum(len(self._tokenize(t.get('text', ''))) for t in low_engagement_tweets) / len(low_engagement_tweets) if low_engagement_tweets else 0
        length_diff = high_length - low_length
        
        # 4. Question usage
        high_questions = sum('?' in t.get('text', '') for t in high_engagement_tweets) / len(high_engagement_tweets) if high_engagement_tweets else 0
        low_questions = sum('?' in t.get('text', '') for t in low_engagement_tweets) / len(low_engagement_tweets) if low_engagement_tweets else 0
        question_diff = high_questions - low_questions
        
        # 5. Analyze most engaging individual tweets
        top_tweets = []
        if sorted_tweets:
            for t in sorted_tweets[:5]:  # Top 5 most engaging tweets
                text = t.get('text', '')
                if not text:
                    continue
                    
                sentiment = self._analyze_sentiment(text)
                reading_ease = textstat.flesch_reading_ease(text)
                words = len(self._tokenize(text))
                
                top_tweets.append({
                    'text': text[:100] + ('...' if len(text) > 100 else ''),
                    'engagement': t.get('total_engagement', 0),
                    'sentiment': sentiment,
                    'readability': reading_ease,
                    'word_count': words,
                    'has_question': '?' in text,
                    'has_exclamation': '!' in text
                })
        
        # Generate insights based on comparisons
        engagement_insights = []
        
        if abs(readability_diff) > 10:
            if readability_diff > 0:
                engagement_insights.append("More engaging tweets are significantly easier to read")
            else:
                engagement_insights.append("More engaging tweets are more complex and sophisticated")
        
        if abs(sentiment_diff) > 0.2:
            if sentiment_diff > 0:
                engagement_insights.append("More positive tweets receive higher engagement")
            else:
                engagement_insights.append("More critical or negative tweets receive higher engagement")
        
        if abs(length_diff) > 5:
            if length_diff > 0:
                engagement_insights.append("Longer, more detailed tweets perform better")
            else:
                engagement_insights.append("Shorter, more concise tweets perform better")
        
        if abs(question_diff) > 0.2:
            if question_diff > 0:
                engagement_insights.append("Tweets with questions drive significantly more engagement")
            else:
                engagement_insights.append("Questions don't contribute to higher engagement")
        
        return {
            "high_vs_low_comparison": {
                "readability": {
                    "high_engagement": high_readability,
                    "low_engagement": low_readability,
                    "difference": readability_diff
                },
                "sentiment": {
                    "high_engagement": high_sentiment,
                    "low_engagement": low_sentiment,
                    "difference": sentiment_diff
                },
                "avg_length": {
                    "high_engagement": high_length,
                    "low_engagement": low_length,
                    "difference": length_diff
                },
                "question_usage": {
                    "high_engagement": high_questions,
                    "low_engagement": low_questions,
                    "difference": question_diff
                }
            },
            "top_engaging_tweets": top_tweets,
            "engagement_insights": engagement_insights
        }
    
    def _analyze_persuasive_patterns(self, tweets: List[Dict]) -> Dict[str, Any]:
        """
        Identify persuasive language patterns in the tweets
        """
        # Combine all tweet text for pattern analysis
        all_text = " ".join(tweet.get('text', '') for tweet in tweets if tweet.get('text'))
        
        if not all_text:
            return {}
        
        # Tokenize text
        words = self._tokenize(all_text)
        
        # Split into sentences
        sentences = self._split_into_sentences(all_text)
        
        # Analyze persuasive markers
        persuasive_counts = {category: 0 for category in set(self.persuasive_markers.values())}
        marker_counts = {}
        
        for marker, category in self.persuasive_markers.items():
            count = sum(1 for s in sentences if marker in s.lower())
            if count > 0:
                persuasive_counts[category] += count
                marker_counts[marker] = count
        
        # Identify rhetorical questions (questions that don't expect answers)
        rhetorical_questions = sum(1 for s in sentences if '?' in s and any(
            phrase in s.lower() for phrase in ['isn\'t it', 'aren\'t we', 'don\'t you', 
                                           'wouldn\'t it', 'shouldn\'t we', 'why not', 'who doesn\'t']))
        
        # Identify call-to-action patterns
        calls_to_action = sum(1 for s in sentences if any(
            cta in s.lower() for cta in ['click', 'subscribe', 'follow', 'like', 
                                      'share', 'retweet', 'sign up', 'join', 'visit']))
        
        # Identify social proof markers
        social_proof = sum(1 for s in sentences if any(
            proof in s.lower() for proof in ['everyone is', 'people are', 'growing number', 
                                         'thousands of', 'millions of', 'trending', 'popular']))
        
        # Determine dominant persuasive style
        if sum(persuasive_counts.values()) > 0:
            dominant_style = max(persuasive_counts.items(), key=lambda x: x[1])[0]
        else:
            dominant_style = "Direct and Plain"
        
        # Generate insights
        persuasive_insights = []
        
        if rhetorical_questions > len(sentences) * 0.1:  # More than 10% are rhetorical questions
            persuasive_insights.append("Heavy use of rhetorical questions to engage audience")
        
        if calls_to_action > len(sentences) * 0.05:  # More than 5% have calls to action
            persuasive_insights.append("Frequently incorporates clear calls-to-action")
        
        if social_proof > 0:
            persuasive_insights.append("Uses social proof to build credibility")
        
        if persuasive_counts.get('imperative', 0) > persuasive_counts.get('suggestive', 0) * 2:
            persuasive_insights.append("Strongly directive tone rather than suggestive")
        elif persuasive_counts.get('suggestive', 0) > persuasive_counts.get('imperative', 0):
            persuasive_insights.append("Prefers suggestion over direct commands")
        
        if persuasive_counts.get('absolutism', 0) > 0:
            persuasive_insights.append("Uses absolute terms (always/never) for emphasis")
        
        if persuasive_counts.get('engagement', 0) > 0:
            persuasive_insights.append("Directly invites audience interaction and thought")
        
        return {
            "persuasive_categories": persuasive_counts,
            "top_markers": {marker: count for marker, count in 
                          sorted(marker_counts.items(), key=lambda x: x[1], reverse=True)[:5]},
            "rhetorical_questions": rhetorical_questions,
            "calls_to_action": calls_to_action,
            "social_proof_markers": social_proof,
            "dominant_style": dominant_style,
            "insights": persuasive_insights
        }
    
    def _extract_practical_insights(self, tweets: List[Dict]) -> Dict[str, Any]:
        """
        Extract practical insights that can be used to improve writing
        or train AI models
        """
        if not tweets:
            return {}
        
        # Combine all text
        all_text = " ".join(tweet.get('text', '') for tweet in tweets if tweet.get('text'))
        
        if not all_text:
            return {}
        
        # Get basic stats
        words = self._tokenize(all_text)
        sentences = self._split_into_sentences(all_text)
        
        # Calculate average sentiment
        avg_sentiment = sum(self._analyze_sentiment(t.get('text', '')) 
                          for t in tweets if t.get('text')) / len(tweets)
        
        # Find emoji usage
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F700-\U0001F77F"  # alchemical symbols
            u"\U0001F780-\U0001F7FF"  # Geometric Shapes
            u"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
            u"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
            u"\U0001FA00-\U0001FA6F"  # Chess Symbols
            u"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
            u"\U00002702-\U000027B0"  # Dingbats
            u"\U000024C2-\U0001F251" 
            "]+", flags=re.UNICODE)
        
        emojis = emoji_pattern.findall(all_text)
        emoji_counts = Counter(emojis)
        top_emojis = emoji_counts.most_common(10)
        
        # Extract significant word patterns
        # Filter out common stop words for meaningful analysis
        significant_words = [w for w in words if w not in self.stop_words and len(w) > 2]
        word_counts = Counter(significant_words)
        
        # Extract vocabulary themes by word type
        # This is a simplified approach without POS tagging
        
        # Words that often function as nouns (simplified approach)
        potential_nouns = [w for w in significant_words 
                         if not w.endswith('ly') and not w.endswith('ing') 
                         and not w in self.first_person and not w in self.second_person
                         and not w in self.third_person]
        
        # Words that often function as verbs (simplified approach)
        potential_verbs = [w for w in significant_words if w.endswith('ing') or w.endswith('ed')]
        
        # Words that often function as adjectives (simplified approach)
        potential_adjectives = [w for w in significant_words if w.endswith('ly')]
        
        # Get top words by type
        top_nouns = Counter(potential_nouns).most_common(10)
        top_verbs = Counter(potential_verbs).most_common(10)
        top_adjectives = Counter(potential_adjectives).most_common(10)
        
        # Generate AI training recommendations
        ai_insights = []
        
        # Style insights based on collected metrics
        sentences_per_tweet = len(sentences) / len(tweets)
        
        if avg_sentiment > 0.3:
            ai_insights.append("Maintain consistently positive tone")
        elif avg_sentiment < -0.3:
            ai_insights.append("Adopt more critical/skeptical voice")
        else:
            ai_insights.append("Balance positive and negative elements")
        
        # Formality insights
        formal_words_count = sum(1 for word in words if word in self.formal_words)
        informal_words_count = sum(1 for word in words if word in self.informal_words)
        
        if formal_words_count > informal_words_count * 2:
            ai_insights.append("Use formal language with proper terminology")
        elif informal_words_count > formal_words_count:
            ai_insights.append("Adopt conversational, casual style with contractions")
        
        # Emoji insights
        if top_emojis:
            emoji_str = " ".join([emoji for emoji, _ in top_emojis[:3]])
            ai_insights.append(f"Incorporate emojis, especially: {emoji_str}")
        
        # Structure insights
        avg_sent_len = sum(len(self._tokenize(s)) for s in sentences) / len(sentences) if sentences else 0
        
        if avg_sent_len < 10:
            ai_insights.append("Use short, punchy sentences of 5-10 words")
        elif avg_sent_len > 20:
            ai_insights.append("Construct longer, more complex sentence structures")
        
        # Question pattern
        question_ratio = sum('?' in s for s in sentences) / len(sentences) if sentences else 0
        if question_ratio > 0.2:  # More than 20% are questions
            ai_insights.append("Frequently use questions to engage audience")
        
        return {
            "vocabulary_themes": {
                "key_nouns": [{"word": word, "count": count} for word, count in top_nouns],
                "key_verbs": [{"word": word, "count": count} for word, count in top_verbs],
                "key_adjectives": [{"word": word, "count": count} for word, count in top_adjectives]
            },
            "emoji_usage": {
                "uses_emoji": bool(top_emojis),
                "top_emojis": [{"emoji": emoji, "count": count} for emoji, count in top_emojis]
            },
            "writing_recommendations": ai_insights,
            "training_focus": {
                "sentiment_focus": "positive" if avg_sentiment > 0.2 else "negative" if avg_sentiment < -0.2 else "neutral",
                "formality": "formal" if formal_words_count > informal_words_count * 2 else 
                           "informal" if informal_words_count > formal_words_count else "neutral",
                "sentence_style": "short" if avg_sent_len < 12 else "medium" if avg_sent_len < 18 else "long",
                "question_frequency": "high" if question_ratio > 0.2 else "medium" if question_ratio > 0.1 else "low"
            }
        }