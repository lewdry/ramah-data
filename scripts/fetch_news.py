import feedparser
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import requests
from bs4 import BeautifulSoup
import json
import os
import time
import logging
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import bisect
import re

# Configuration
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/rss.xml",  # BBC News - Top Stories
    "https://www.abc.net.au/news/feed/45910/rss.xml",  # ABC News (Au) - Top Stories
    "https://www.theguardian.com/world/rss",  # The Guardian - World News
    "https://www.sbs.com.au/news/feed",  # SBS News
    "https://feeds.arstechnica.com/arstechnica/index",  # ArsTechnica
    "https://feedx.net/rss/ap.xml",  # AP News
    "https://feeds.npr.org/1001/rss.xml",  # NPR News
 ]
# Mapping from identifying substring (usually in feed URL or link) to
# canonical publisher name. Add more entries here as new feeds are added.
SOURCE_MAP = {
    'abc.net.au': 'ABC News',
    'feeds.bbci.co.uk': 'BBC News',
    'bbc.co.uk': 'BBC News',
    'bbc.com': 'BBC News',
    'theguardian.com': 'The Guardian',
    'sbs.com.au': 'SBS News',
    'arstechnica.com': 'Ars Technica',
    'feedx.net/rss/ap.xml': 'AP News',
    'feeds.npr.org': 'NPR News',
}

SENTIMENT_THRESHOLD = 0.5
BLOCK_LIST = ["kill", "bomb", "murder", "rampage", "fatal", "trump", "ICE", "Israel", ]
MAX_STORIES = 250
# Use `docs/` as the storage directory
DATA_DIR = "docs"
DATA_FILE = os.path.join(DATA_DIR, "good_news.json")
ARCHIVE_FILE = os.path.join(DATA_DIR, "old_news.json")
LOG_FILE = os.path.join(DATA_DIR, "fetch.log")

# Setup Logging
os.makedirs(DATA_DIR, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

def get_first_sentence(url):
    """
    Fetches the article content and attempts to extract the first sentence.
    Falls back to None if extraction fails.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Heuristics for finding article text based on common structures
        paragraphs = soup.find_all('p')
        
        ignored_phrases = [
            "Copyright", 
            "Find any issues using dark mode", 
            "Use BBC", 
            "terms of use",
            "privacy policy"
        ]

        for p in paragraphs:
            text = p.get_text().strip()
            
            # Skip if any ignored phrase is in the text
            if any(phrase in text for phrase in ignored_phrases):
                continue

            # Simple filter to avoid menu items, copyright notices, etc.
            # Increased length check slightly and check for end punctuation
            if len(text) > 60 and text[-1] in ['.', '!', '?']:
                # Split by dot to get the first sentence (naively)
                first_sentence = text.split('. ')[0].rstrip('.') + '.'
                return first_sentence
                
    except Exception as e:
        logging.warning(f"Failed to fetch content for {url}: {e}")
        return None
    
    return None

def load_data(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.error(f"JSON decode error in {filename}. Starting fresh.")
            return []
    return []


def canonical_source(feed_url, feed_title=None, link=None):
    """Return a canonical source name given the feed URL, feed title, or link.

    The priority is:
    1) Match a known substring in `feed_url` against `SOURCE_MAP`.
    2) Clean up and prefer the feed title (strip suffixes like " - Top Stories").
    3) Match a known substring in the article `link` against `SOURCE_MAP`.
    4) Fallback to deriving from the link's domain or the provided feed title.
    """
    # 1) Match by feed URL
    for key, name in SOURCE_MAP.items():
        if key in (feed_url or ''):
            return name

    # 2) Prefer cleaned feed title when it's not generic like "Top Stories"
    if feed_title:
        t = feed_title.strip()
        if ' - ' in t:
            t = t.split(' - ', 1)[0].strip()
        if t and t.lower() != 'top stories':
            return t

    # 3) Try matching by article link
    if link:
        for key, name in SOURCE_MAP.items():
            if key in link:
                return name
        m = re.search(r'https?://([^/]+)/', link)
        if m:
            domain = m.group(1)
            if 'abc.net.au' in domain:
                return 'ABC News'
            if 'bbc.' in domain:
                return 'BBC News'
            if 'theguardian.com' in domain:
                return 'The Guardian'
            if 'sbs.com.au' in domain:
                return 'SBS News'
            if 'arstechnica.com' in domain:
                return 'Ars Technica'
            if 'npr.org' in domain:
                return 'NPR News'

    # 4) Fallback
    return feed_title or 'Unknown Source'


def _parse_timestamp_to_epoch(ts):
    """Parse various timestamp formats into a UTC epoch (float seconds).
    Returns 0 on failure so items without timestamps sort to the end.
    Handles RFC 2822/RSS dates via parsedate_to_datetime, ISO8601 with or
    without a colon in the timezone offset, and trailing Z.
    """
    if not ts:
        return 0.0

    # Try email.utils first (works for many feed timestamps)
    try:
        dt = parsedate_to_datetime(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).timestamp()
    except Exception:
        pass

    # Normalize ISO8601 timezone offsets like +1100 to +11:00
    iso = ts
    m = re.search(r"([+-]\d{4})$", ts)
    if m:
        tz = m.group(1)
        iso = ts[:-5] + tz[:3] + ':' + tz[3:]

    # Handle Z suffix
    if iso.endswith('Z'):
        iso = iso[:-1] + '+00:00'

    try:
        dt = datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).timestamp()
    except Exception:
        logging.debug(f"Could not parse timestamp '{ts}'")
        return 0.0


def _ensure_reverse_chrono_sorted(items):
    """Return a new list sorted reverse-chronologically (newest first).
    Uses parsed timestamps and falls back to original order for ties.
    """
    paired = []
    for i, itm in enumerate(items):
        epoch = _parse_timestamp_to_epoch(itm.get('timestamp'))
        # Use tuple ( -epoch, i ) so newer items (larger epoch) sort first and
        # tie-breaker keeps original relative order.
        paired.append(( -epoch, i, itm ))

    paired.sort()
    return [p[2] for p in paired]

def save_data(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def archive_old_stories(new_archived_stories):
    if not new_archived_stories:
        return
    
    archive_data = load_data(ARCHIVE_FILE)
    # Use a set for quick deduplication based on 'link'
    existing_links = {item['link'] for item in archive_data}
    
    added_to_archive = 0
    for story in new_archived_stories:
        if story['link'] not in existing_links:
            archive_data.append(story)
            existing_links.add(story['link'])
            added_to_archive += 1
    
    if added_to_archive > 0:
        # Sort archive by timestamp descending using parsed epochs. This
        # ensures mixed timestamp formats are sorted correctly and that
        # the archive contains the true oldest stories at the end.
        archive_data = _ensure_reverse_chrono_sorted(archive_data)
        save_data(archive_data, ARCHIVE_FILE)
        logging.info(f"Archived {added_to_archive} new stories to {ARCHIVE_FILE}.")

def main():
    logging.info("Starting Ramah News Fetcher")
    analyzer = SentimentIntensityAnalyzer()
    
    current_data = load_data(DATA_FILE)

    # Ensure existing data is reverse-chronologically sorted and build
    # a helper list of negative epochs for insertion (negatives make it
    # suitable for bisect on ascending order).
    current_data = _ensure_reverse_chrono_sorted(current_data)
    neg_epochs = [ -_parse_timestamp_to_epoch(item.get('timestamp')) for item in current_data ]

    # Create a set of existing URLs for fast deduplication
    existing_urls = {item['link'] for item in current_data}

    new_stories_count = 0

    for feed_url in RSS_FEEDS:
        logging.info(f"Checking feed: {feed_url}")
        try:
            # Use requests with a User-Agent to avoid 403 Forbidden errors
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            response = requests.get(feed_url, headers=headers, timeout=10)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except Exception as e:
            logging.error(f"Error fetching feed {feed_url}: {e}")
            continue
            
        if feed.bozo:
            # Check if it's just a warning or a fatal error
            if isinstance(feed.bozo_exception, (feedparser.CharacterEncodingOverride, feedparser.NonXMLContentType)):
                logging.warning(f"Feed {feed_url} has a parsing warning: {feed.bozo_exception}. Proceeding anyway.")
            else:
                logging.error(f"Error parsing feed {feed_url}: {feed.bozo_exception}")
                continue
            
        for entry in feed.entries:
            link = entry.get('link')
            
            if link in existing_urls:
                continue
            
            title = entry.get('title', '')
            
            # Block list check
            if any(blocked_word.lower() in title.lower() for blocked_word in BLOCK_LIST):
                logging.debug(f"Skipping blocked headline: {title}")
                continue
            
            # Sentiment Analysis
            # 1. VADER
            vader_score = analyzer.polarity_scores(title)['compound']
            
            # 2. TextBlob
            textblob_score = TextBlob(title).sentiment.polarity
            
            # 3. Mean
            mean_score = (vader_score + textblob_score) / 2
            
            if mean_score > SENTIMENT_THRESHOLD:
                logging.info(f"Found good news: {title} (Mean Score: {mean_score:.4f}, VADER: {vader_score:.4f}, TextBlob: {textblob_score:.4f})")
                
                # Fetch first sentence
                first_sentence = get_first_sentence(link)
                
                # If scraping failed, try using description/summary from RSS
                if not first_sentence:
                    summary = entry.get('summary') or entry.get('description', '')
                    if summary:
                         # Strip HTML from summary if present
                        soup_summary = BeautifulSoup(summary, 'html.parser')
                        text_summary = soup_summary.get_text().strip()
                        if text_summary:
                            first_sentence = text_summary.split('.')[0] + '.'
                
                # Get publication time from feed, fallback to current time
                # Convert everything to UTC for consistent sorting
                published_parsed = entry.get('published_parsed')
                if published_parsed:
                    # published_parsed is a time.struct_time in UTC
                    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", published_parsed)
                else:
                    # Fallback to current time in UTC
                    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

                # Determine canonical source name using prioritized heuristics
                source = canonical_source(feed_url, feed.feed.get('title', 'Unknown Source'), link)

                news_item = {
                    'headline': title,
                    'link': link,
                    'mean_score': round(mean_score, 4),
                    'vader_score': round(vader_score, 4),
                    'textblob_score': round(textblob_score, 4),
                    'first_sentence': first_sentence or "Summary not available.",
                    'timestamp': timestamp,
                    'source': source
                }
                
                # Insert story in the correctly-sorted position by timestamp.
                # We compute its epoch and insert using bisect to keep the
                # list reverse-chronological (newest first). For identical
                # timestamps we insert after existing equal timestamps so
                # the newest-arrived stories appear after earlier ones with
                # the same published time.
                story_epoch = _parse_timestamp_to_epoch(news_item.get('timestamp'))
                insert_key = -story_epoch
                idx = bisect.bisect_right(neg_epochs, insert_key)
                neg_epochs.insert(idx, insert_key)
                current_data.insert(idx, news_item)

                existing_urls.add(link)
                new_stories_count += 1

    if new_stories_count > 0:
        # Trim/keep the most recent MAX_STORIES (current_data is already
        # reverse-chronological due to insertion logic)
        keep_stories = current_data[:MAX_STORIES]
        archive_stories = current_data[MAX_STORIES:]

        save_data(keep_stories, DATA_FILE)
        logging.info(f"Saved {len(keep_stories)} stories to {DATA_FILE}.")

        if archive_stories:
            archive_old_stories(archive_stories)
    else:
        logging.info("No new positive stories found.")

if __name__ == "__main__":
    main()
