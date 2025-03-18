"""
SocialScope-Tweets Web UI - Flask Application
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
import threading
import queue
from werkzeug.exceptions import HTTPException
import traceback

# Add project root to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import from the core project
from src.core.socialdata_client import SocialDataClient
from src.core.tweet_fetcher import TweetFetcher
from src.core.tweet_processor import TweetProcessor
from src.core.output_generator import OutputGenerator

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Add the current date to all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('web_ui.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global job tracking
active_jobs = {}
job_results = {}
job_logs = {}

def run_analysis_job(job_id, username, tweet_type, max_tweets, start_date, end_date):
    """Run analysis job in background thread with improved error handling"""
    try:
        job_logs[job_id] = []
        
        def log_message(message):
            """Add message to job logs"""
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            job_logs[job_id].append(f"[{timestamp}] {message}")
            logger.info(f"Job {job_id}: {message}")
        
        log_message(f"Starting analysis for @{username}")
        
        # Initialize components with better error handling
        try:
            client = SocialDataClient()
            fetcher = TweetFetcher(client)
            processor = TweetProcessor()
            output_gen = OutputGenerator("output")
        except Exception as e:
            log_message(f"Error initializing components: {str(e)}")
            raise
            
        # Step 1: Fetch account info
        log_message(f"Fetching account info for @{username}")
        try:
            account_info = fetcher.fetch_user_info(username)
            log_message(f"Account: {account_info['name']} (@{account_info['screen_name']})")
            log_message(f"Followers: {account_info['followers_count']:,}, Following: {account_info['friends_count']:,}")
            log_message(f"Tweets: {account_info['statuses_count']:,}")
        except Exception as e:
            log_message(f"Error fetching account info: {str(e)}")
            raise
        
        # Step 2: Create output folder
        try:
            output_folder = output_gen.create_output_folder(username)
            relative_output_path = os.path.relpath(output_folder, "output")
            log_message(f"Created output folder: {output_folder}")
        except Exception as e:
            log_message(f"Error creating output folder: {str(e)}")
            raise
        
        # Step 3: Save account info
        try:
            output_gen.save_account_info(account_info, output_folder)
        except Exception as e:
            log_message(f"Error saving account info: {str(e)}")
            raise
        
        # Step 4: Fetch tweets with progress updates
        log_message(f"Fetching tweets for @{username}")
        try:
            tweets = fetcher.fetch_user_tweets(
                username,
                tweet_type=tweet_type,
                max_tweets=max_tweets,
                start_date=start_date,
                end_date=end_date
            )
            log_message(f"Fetched {len(tweets)} tweets")
        except Exception as e:
            log_message(f"Error fetching tweets: {str(e)}")
            raise
        
        # Step 5: Process tweets
        log_message("Processing tweets...")
        try:
            processed_tweets = processor.process_tweets(tweets)
        except Exception as e:
            log_message(f"Error processing tweets: {str(e)}")
            raise
        
        # Step 6: Extract topics
        log_message("Extracting topics...")
        try:
            topics = processor.extract_topics(processed_tweets)
            log_message(f"Found {len(topics)} topics: {', '.join(topics)}")
        except Exception as e:
            log_message(f"Error extracting topics: {str(e)}")
            raise
        
        # Step 7: Tag tweets
        log_message("Tagging tweets with topics and sentiment...")
        try:
            tagged_tweets = processor.tag_tweets(processed_tweets, topics)
        except Exception as e:
            log_message(f"Error tagging tweets: {str(e)}")
            raise
        
        # Step 8: Save to different formats
        log_message("Saving tweets to output formats...")
        
        csv_simple = ""
        csv_analysis = ""
        xml_file = ""
        summary_file = ""
        
        # Save simple CSV
        try:
            csv_simple = output_gen.save_tweets_to_csv(tagged_tweets, output_folder, simple=True)
            log_message(f"Saved simple CSV: {os.path.basename(csv_simple)}")
        except Exception as e:
            log_message(f"Error saving simple CSV: {str(e)}")
            # Continue with other formats
        
        # Save analysis CSV
        try:
            csv_analysis = output_gen.save_tweets_to_csv(tagged_tweets, output_folder, simple=False)
            log_message(f"Saved analysis CSV: {os.path.basename(csv_analysis)}")
        except Exception as e:
            log_message(f"Error saving analysis CSV: {str(e)}")
        
        # Save lean XML with style analysis
        try:
            xml_file = output_gen.save_tweets_to_xml(tagged_tweets, output_folder, account_info)
            log_message(f"Saved XML: {os.path.basename(xml_file)}")
        except Exception as e:
            log_message(f"Error saving XML: {str(e)}")
        
        # Generate human-readable summary text
        try:
            summary_file = output_gen.save_summary_text(tagged_tweets, output_folder, account_info)
            log_message(f"Saved summary: {os.path.basename(summary_file)}")
        except Exception as e:
            log_message(f"Error saving summary: {str(e)}")
        
        # Step 9: Prepare result data for display
        summary_content = ""
        
        if summary_file:
            try:
                with open(summary_file, 'r', encoding='utf-8') as f:
                    summary_content = f.read()
            except Exception as e:
                log_message(f"Error reading summary file: {str(e)}")
        
        # Store results
        job_results[job_id] = {
            'status': 'completed',
            'username': username,
            'tweet_count': len(tweets),
            'output_folder': str(output_folder),
            'relative_path': relative_output_path,
            'files': {
                'csv_simple': os.path.basename(csv_simple) if csv_simple else "",
                'csv_analysis': os.path.basename(csv_analysis) if csv_analysis else "",
                'xml': os.path.basename(xml_file) if xml_file else "",
                'summary': os.path.basename(summary_file) if summary_file else "",
                'account_info': "account_info.json"
            },
            'summary_content': summary_content,
            'account_info': {
                'name': account_info.get('name', ''),
                'screen_name': account_info.get('screen_name', ''),
                'followers': account_info.get('followers_count', 0),
                'following': account_info.get('friends_count', 0),
                'tweets': account_info.get('statuses_count', 0),
                'profile_image': account_info.get('profile_image_url_https', '')
            }
        }
        
        log_message("Analysis completed successfully!")
        
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"Error in job {job_id}: {str(e)}\n{error_details}")
        job_results[job_id] = {
            'status': 'error',
            'error_message': str(e),
            'error_details': error_details
        }
        if job_id in job_logs:
            job_logs[job_id].append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERROR: {str(e)}")
    
    finally:
        # Remove from active jobs
        if job_id in active_jobs:
            del active_jobs[job_id]

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Submit a new analysis job"""
    username = request.form.get('username', '').strip()
    if not username:
        flash("Please enter a valid Twitter username", "error")
        return redirect(url_for('index'))
    
    # Remove @ symbol if included
    if username.startswith('@'):
        username = username[1:]
    
    # Get job parameters
    tweet_type = request.form.get('tweet_type', 'both')
    max_tweets = int(request.form.get('max_tweets', 1000))
    
    # Parse dates if provided
    start_date = None
    end_date = None
    
    start_date_str = request.form.get('start_date', '')
    end_date_str = request.form.get('end_date', '')
    
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            flash("Invalid start date format. Please use YYYY-MM-DD", "error")
            return redirect(url_for('index'))
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
        except ValueError:
            flash("Invalid end date format. Please use YYYY-MM-DD", "error")
            return redirect(url_for('index'))
    
    # Create a job ID
    job_id = f"{username}_{int(time.time())}"
    
    # Start job in a separate thread
    job_thread = threading.Thread(
        target=run_analysis_job,
        args=(job_id, username, tweet_type, max_tweets, start_date, end_date),
        daemon=True
    )
    
    active_jobs[job_id] = {
        'start_time': datetime.now(),
        'username': username,
        'status': 'running'
    }
    
    job_thread.start()
    
    # Redirect to job status page
    return redirect(url_for('job_status', job_id=job_id))

# Utility function for dashboard data preparation
def prepare_dashboard_data(tweets, account_info):
    """
    Prepare structured data for the dashboard
    """
    if not tweets:
        return {}
    
    # Extract basic metrics
    tweet_count = len(tweets)
    reply_count = sum(1 for t in tweets if t.get('in_reply_to_status_id_str') is not None)
    retweet_count = sum(1 for t in tweets if t.get('retweeted_status') is not None)
    
    # Calculate percentages
    reply_percentage = (reply_count / tweet_count) * 100 if tweet_count > 0 else 0
    retweet_percentage = (retweet_count / tweet_count) * 100 if tweet_count > 0 else 0
    
    # Calculate engagement metrics
    total_likes = sum(t.get('favorite_count', 0) or 0 for t in tweets)
    total_retweets = sum(t.get('retweet_count', 0) or 0 for t in tweets)
    total_replies = sum(t.get('reply_count', 0) or 0 for t in tweets)
    
    avg_likes = total_likes / tweet_count if tweet_count > 0 else 0
    avg_retweets = total_retweets / tweet_count if tweet_count > 0 else 0
    avg_replies = total_replies / tweet_count if tweet_count > 0 else 0
    
    # Prepare simplified tweet list for table view
    dashboard_tweets = []
    for tweet in tweets[:100]:  # Limit to latest 100 tweets for performance
        # Skip retweets as they don't have as much analytical value
        if tweet.get('retweeted_status'):
            continue
            
        created_at = tweet.get('tweet_created_at', '') or tweet.get('created_at', '')
        text = tweet.get('full_text', '') or tweet.get('text', '')
        
        # Calculate engagement score
        engagement = (tweet.get('favorite_count', 0) or 0) + \
                    ((tweet.get('retweet_count', 0) or 0) * 2) + \
                    ((tweet.get('reply_count', 0) or 0) * 3)
        
        # Determine sentiment (this would come from your analysis)
        # In a real implementation, this would be from your processing pipeline
        sentiment = "neutral"
        if 'sentiment' in tweet.get('tags', {}):
            sentiment = tweet.get('tags', {}).get('sentiment')
            
        # Extract topics
        topics = []
        if 'topics' in tweet.get('tags', {}):
            topics = tweet.get('tags', {}).get('topics', [])
        
        dashboard_tweets.append({
            'id': tweet.get('id_str', ''),
            'created_at': created_at,
            'text': text,
            'engagement': engagement,
            'sentiment': sentiment,
            'topics': topics,
            'is_reply': tweet.get('in_reply_to_status_id_str') is not None
        })
    
    # Sort by engagement for high-impact tweets
    dashboard_tweets.sort(key=lambda x: x['engagement'], reverse=True)
    
    return {
        'metrics': {
            'tweet_count': tweet_count,
            'reply_percentage': reply_percentage,
            'retweet_percentage': retweet_percentage,
            'avg_likes': avg_likes,
            'avg_retweets': avg_retweets,
            'avg_replies': avg_replies
        },
        'tweets': dashboard_tweets,
        'account': {
            'name': account_info.get('name', ''),
            'screen_name': account_info.get('screen_name', ''),
            'followers_count': account_info.get('followers_count', 0),
            'friends_count': account_info.get('friends_count', 0),
            'statuses_count': account_info.get('statuses_count', 0),
            'profile_image_url': account_info.get('profile_image_url_https', '')
        }
    }

@app.route('/job/<job_id>')
def job_status(job_id):
    """Show job status page"""
    # Check if the job exists
    if job_id not in active_jobs and job_id not in job_results:
        flash("Job not found", "error")
        return redirect(url_for('index'))
    
    # If job is complete, show results
    if job_id in job_results:
        result = job_results[job_id]
        logs = job_logs.get(job_id, [])
        
        # If it was successful, render the results template with dashboard data
        if result['status'] == 'completed':
            # Get the analysis results path
            output_folder = result['output_folder']
            
            # Load tweet data if available (for interactive dashboard)
            dashboard_data = {}
            try:
                with open(os.path.join(output_folder, 'dashboard_data.json'), 'r', encoding='utf-8') as f:
                    dashboard_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                # If dashboard data doesn't exist, we'll use the data we have
                logger.info("Dashboard data not found, using available data")
                dashboard_data = {}
            
            return render_template('results.html', 
                                result=result, 
                                logs=logs, 
                                job_id=job_id,
                                dashboard_data=dashboard_data)
        
        # If job failed, show error page
        elif result['status'] == 'error':
            return render_template('job_status.html', 
                                error=True,
                                error_message=result.get('error_message', 'Unknown error'),
                                logs=logs,
                                job_id=job_id)
    
    # If job is still running, show status page
    return render_template('job_status.html', job_id=job_id, logs=job_logs.get(job_id, []), error=False)

@app.route('/api/job_status/<job_id>')
def api_job_status(job_id):
    """API endpoint to get job status for AJAX polling"""
    status = "not_found"
    progress = 0
    message = "Job not found"
    
    if job_id in active_jobs:
        status = "running"
        message = f"Analyzing tweets for @{active_jobs[job_id]['username']}..."
    elif job_id in job_results:
        status = job_results[job_id]['status']
        message = "Analysis complete" if status == "completed" else job_results[job_id].get('error_message', 'Analysis failed')
    
    logs = job_logs.get(job_id, [])
    
    return jsonify({
        "status": status,
        "message": message,
        "logs": logs[-10:] if logs else []  # Return last 10 logs
    })

@app.route('/download/<path:job_path>/<filename>')
def download_file(job_path, filename):
    """Download a result file"""
    directory = os.path.join('output', job_path)
    return send_from_directory(directory, filename, as_attachment=True)

@app.route('/jobs')
def list_jobs():
    """List all completed jobs"""
    completed_jobs = []
    
    for job_id, result in job_results.items():
        if result['status'] == 'completed':
            completed_jobs.append({
                'job_id': job_id,
                'username': result['username'],
                'tweet_count': result['tweet_count'],
                'date': job_id.split('_')[-1]  # Extract timestamp from job ID
            })
    
    return render_template('jobs.html', jobs=completed_jobs)

# -----------------------------
#   Custom Error Handlers
# -----------------------------
@app.errorhandler(404)
def page_not_found(e):
    return render_template(
        'error.html',
        error_code=404,
        error_message="Page Not Found",
        error_details="The requested page does not exist."
    ), 404

@app.errorhandler(500)
def server_error(e):
    # Log the error for debugging
    app.logger.error(f"500 error: {str(e)}\n{traceback.format_exc()}")
    return render_template(
        'error.html',
        error_code=500,
        error_message="Server Error",
        error_details="Something went wrong on our end. Please try again later."
    ), 500

@app.errorhandler(Exception)
def handle_exception(e):
    # Log the error
    app.logger.error(f"Unhandled exception: {str(e)}\n{traceback.format_exc()}")
    
    # Handle HTTP exceptions differently
    if isinstance(e, HTTPException):
        return render_template(
            'error.html',
            error_code=e.code,
            error_message=e.name,
            error_details=e.description
        ), e.code
    
    # For non-HTTP exceptions, return a 500 error
    return render_template(
        'error.html',
        error_code=500,
        error_message="Unexpected Error",
        error_details="An unexpected error occurred. Our team has been notified."
    ), 500

# -----------------------------
#   Datetime Filter
# -----------------------------
@app.template_filter('datetime')
def format_datetime(timestamp):
    """Format a timestamp as a readable date"""
    date = datetime.fromtimestamp(int(timestamp))
    return date.strftime('%B %d, %Y %H:%M')

# -----------------------------
#   Main Entry
# -----------------------------
if __name__ == '__main__':
    # Make sure output directory exists
    os.makedirs('output', exist_ok=True)
    # Run Flask app
    app.run(debug=True, host='0.0.0.0', port=8000)