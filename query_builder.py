# query_builder.py
#!/usr/bin/env python3
from enhanced_scraper import TwitterQueryBuilder
from datetime import datetime, timedelta

def build_example_queries():
    """Build and print example queries"""
    # Example 1: Basic user tweets
    builder = TwitterQueryBuilder()
    query1 = builder.from_user("elonmusk").exclude_replies().build()
    print(f"1. Get tweets from Elon Musk (no replies):\n   {query1}\n")
    
    # Example 2: Filtered by engagement
    builder = TwitterQueryBuilder()
    query2 = builder.from_user("elonmusk").min_likes(1000).build()
    print(f"2. Get popular tweets from Elon Musk (1000+ likes):\n   {query2}\n")
    
    # Example 3: Date range
    builder = TwitterQueryBuilder()
    today = datetime.now()
    thirty_days_ago = today - timedelta(days=30)
    query3 = builder.from_user("elonmusk").since_date(thirty_days_ago).until_date(today).build()
    print(f"3. Get Elon Musk tweets from the last 30 days:\n   {query3}\n")
    
    # Example 4: Tweets mentioning a specific user
    builder = TwitterQueryBuilder()
    query4 = builder.mentioning("Tesla").is_verified().build()
    print(f"4. Get verified users mentioning Tesla:\n   {query4}\n")
    
    # Example 5: Tweets with media from a specific user
    builder = TwitterQueryBuilder()
    query5 = builder.from_user("NASA").has_images().build()
    print(f"5. Get NASA tweets with images:\n   {query5}\n")
    
    # Example 6: Keywords and exclusions
    builder = TwitterQueryBuilder()
    query6 = (builder.keyword("python")
                    .exclude_keyword("javascript")
                    .min_retweets(10)
                    .build())
    print(f"6. Get Python tweets (excluding JavaScript) with 10+ retweets:\n   {query6}\n")
    
    # Example 7: Complex combination
    builder = TwitterQueryBuilder()
    one_week_ago = today - timedelta(days=7)
    query7 = (builder.from_user("elonmusk")
                    .keyword("AI")
                    .since_date(one_week_ago)
                    .min_likes(500)
                    .build())
    print(f"7. Get Elon Musk tweets about AI from the last week with 500+ likes:\n   {query7}\n")

if __name__ == "__main__":
    print("=== Twitter Query Builder Examples ===\n")
    build_example_queries()
    
    print("=== Custom Query Builder ===\n")
    print("Now let's build a custom query:")
    
    builder = TwitterQueryBuilder()
    
    # Get user input
    username = input("Enter username (leave empty to skip): ")
    if username:
        builder.from_user(username)
    
    keyword = input("Enter keyword to search for (leave empty to skip): ")
    if keyword:
        builder.keyword(keyword)
    
    exclude = input("Enter keyword to exclude (leave empty to skip): ")
    if exclude:
        builder.exclude_keyword(exclude)
    
    min_likes = input("Enter minimum likes (leave empty to skip): ")
    if min_likes:
        builder.min_likes(int(min_likes))
    
    days_ago = input("Enter how many days back to search (leave empty to skip): ")
    if days_ago:
        days = int(days_ago)
        since_date = datetime.now() - timedelta(days=days)
        builder.since_date(since_date)
    
    media_type = input("Include media? (images/videos/all/none): ").lower()
    if media_type == 'images':
        builder.has_images()
    elif media_type == 'videos':
        builder.has_videos()
    elif media_type == 'all':
        builder.has_media()
    
    # Build and show the query
    final_query = builder.build()
    print("\nYour custom query:")
    print(final_query)