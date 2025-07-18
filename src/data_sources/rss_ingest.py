# src/data_sources/rss_ingest.py
import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging

logger = logging.getLogger("market_aggregator.rss")

class RSSIngest:
    """
    Handles RSS feed ingestion using proper feedparser library
    instead of fragile regex parsing
    """
    
    def __init__(self):
        self.feeds = [
            ('Federal Reserve - Commercial Paper', 'https://www.federalreserve.gov/feeds/Data/CP_OUTST.xml'),
            ('Federal Reserve - Press Monetary', 'https://www.federalreserve.gov/feeds/press_monetary.xml'),
            ('Fox News Latest', 'https://feeds.feedburner.com/foxnews/latest'),
            ('The Hill Home News', 'https://thehill.com/homenews/feed/'),
            ('Daily Caller', 'https://dailycaller.com/feed/'),
            ('Daily Wire', 'https://www.dailywire.com/feeds/rss.xml'),
            ('The Blaze', 'https://www.theblaze.com/feeds/feed.rss'),
            ('News Busters', 'https://newsbusters.org/blog/feed'),
            ('Daily Signal', 'https://www.dailysignal.com/feed'),
            ('Newsmax Headlines', 'https://www.newsmax.com/rss/Headline/76'),
            ('Newsmax Finance', 'https://www.newsmax.com/rss/FinanceNews/4'),
            ('Newsmax Economy', 'https://www.newsmax.com/rss/Economy/2'),
            ('Newsmax World', 'https://www.newsmax.com/rss/GlobalTalk/162'),
            ('Newsmax US', 'https://www.newsmax.com/rss/US/18'),
            ('Newsmax Tech', 'https://www.newsmax.com/rss/SciTech/20'),
            ('Newsmax Wire', 'https://www.newsmax.com/rss/TheWire/118'),
            ('Newsmax Politics', 'https://www.newsmax.com/rss/Politics/1'),
            ('MarketWatch Top Stories', 'https://feeds.content.dowjones.io/public/rss/mw_topstories'),
            ('MarketWatch Real-time', 'https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines'),
            ('MarketWatch Market Pulse', 'https://feeds.content.dowjones.io/public/rss/mw_marketpulse'),
            ('CNBC Markets', 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664'),
            ('CNBC Finance', 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258'),
            ('CNBC Economy', 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=19854910')
        ]
        
        self.session = requests.Session()
        # Use a more realistic browser User-Agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })

    def parse_single_feed(self, source_name: str, feed_url: str, max_articles: int = 5) -> Tuple[str, List[Dict]]:
        """
        Parse a single RSS feed using feedparser (much more reliable than regex)
        
        Returns:
            Tuple of (status_message, list_of_articles)
        """
        try:
            logger.info(f"Fetching feed: {source_name}")
            
            # Add small delay for rate limiting (especially for same-domain requests)
            import time
            import urllib.parse
            
            # Extract domain for rate limiting
            domain = urllib.parse.urlparse(feed_url).netloc
            if 'newsmax.com' in domain:
                # Extra delay for Newsmax since they seem to be rate limiting
                time.sleep(2)
                # Shorter timeout for known problematic feeds
                timeout = 10
            else:
                timeout = 15
            
            # Fetch the feed with appropriate timeout
            response = self.session.get(feed_url, timeout=timeout)
            
            # Check for rate limiting responses
            if response.status_code == 429:
                logger.warning(f"{source_name}: Rate limited (429), retrying after delay...")
                time.sleep(5)
                response = self.session.get(feed_url, timeout=timeout)
            
            response.raise_for_status()
            
            # Parse with feedparser - handles all the XML complexity for us
            feed = feedparser.parse(response.content)
            
            # Check if feed was parsed successfully
            if hasattr(feed, 'bozo') and feed.bozo:
                logger.warning(f"Feed {source_name} has parsing issues: {feed.bozo_exception}")
            
            articles = []
            
            # Process entries (feedparser handles both RSS and Atom feeds)
            for entry in feed.entries[:max_articles]:
                # Extract title
                title = getattr(entry, 'title', 'No title').strip()
                
                # Extract description/summary (feedparser handles CDATA automatically)
                description = ""
                if hasattr(entry, 'description'):
                    description = entry.description
                elif hasattr(entry, 'summary'):
                    description = entry.summary
                
                # Clean HTML tags from description
                if description:
                    import re
                    description = re.sub(r'<[^>]+>', '', description)
                    description = description.strip()
                    if len(description) > 300:
                        description = description[:300] + "..."
                
                # Extract date (feedparser normalizes date formats)
                pub_date = "No date"
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6]).isoformat()
                elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                    pub_date = datetime(*entry.updated_parsed[:6]).isoformat()
                
                # Only add if we have a meaningful title
                if title and title != 'No title' and len(title) > 3:
                    articles.append({
                        'title': title,
                        'description': description,
                        'date': pub_date,
                        'source': source_name,
                        'link': getattr(entry, 'link', '')
                    })
            
            status = f"✅ {source_name} ({len(articles)} articles)"
            logger.info(f"Successfully parsed {len(articles)} articles from {source_name}")
            return status, articles
            
        except requests.exceptions.Timeout:
            error_msg = f"❌ {source_name}: Timeout after {timeout} seconds"
            logger.error(error_msg)
            return error_msg, []
            
        except requests.exceptions.RequestException as e:
            error_msg = f"❌ {source_name}: Network error - {str(e)}"
            logger.error(error_msg)
            return error_msg, []
            
        except Exception as e:
            error_msg = f"❌ {source_name}: Parse error - {str(e)}"
            logger.error(error_msg)
            return error_msg, []

    def fetch_all_feeds(self) -> Tuple[List[Dict], List[str]]:
        """
        Fetch all RSS feeds sequentially (will make async in next phase)
        
        Returns:
            Tuple of (all_articles, feed_statuses)
        """
        all_articles = []
        feed_statuses = []
        
        logger.info(f"Starting to fetch {len(self.feeds)} RSS feeds...")
        
        for source_name, feed_url in self.feeds:
            status, articles = self.parse_single_feed(source_name, feed_url)
            feed_statuses.append(status)
            all_articles.extend(articles)
        
        logger.info(f"Completed RSS ingestion: {len(all_articles)} total articles")
        return all_articles, feed_statuses
    
    def __del__(self):
        """Clean up session when object is destroyed"""
        if hasattr(self, 'session'):
            self.session.close()
