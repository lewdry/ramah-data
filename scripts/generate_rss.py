import json
import os
from datetime import datetime
from xml.sax.saxutils import escape

def generate_rss_feed(json_file, xml_file, feed_title, feed_description):
    """Generate an RSS 2.0 XML feed from a JSON news file."""
    
    if not os.path.exists(json_file):
        print(f"Warning: {json_file} not found. Skipping RSS generation.")
        return
    
    # Load the JSON data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both wrapped format (dict with 'stories') and legacy format (list)
    if isinstance(data, dict):
        stories = data.get('stories', [])
        last_build_date = data.get('last run', datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'))
    else:
        stories = data
        last_build_date = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Convert ISO timestamp to RFC 822 format for RSS
    try:
        dt = datetime.strptime(last_build_date, '%Y-%m-%dT%H:%M:%SZ')
        last_build_date_rfc822 = dt.strftime('%a, %d %b %Y %H:%M:%S GMT')
    except:
        last_build_date_rfc822 = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # Start building the RSS XML
    rss_items = []
    for story in stories:
        headline = escape(story.get('headline', ''))
        link = escape(story.get('link', ''))
        description = escape(story.get('first_sentence', 'No description available.'))
        source = escape(story.get('source', 'Unknown Source'))
        pub_date = story.get('timestamp', '')
        
        # Convert ISO timestamp to RFC 822 for RSS pubDate
        try:
            dt = datetime.strptime(pub_date, '%Y-%m-%dT%H:%M:%SZ')
            pub_date_rfc822 = dt.strftime('%a, %d %b %Y %H:%M:%S GMT')
        except:
            pub_date_rfc822 = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # Build RSS item
        item = f"""    <item>
      <title>{headline}</title>
      <link>{link}</link>
      <description>{description}</description>
      <source>{source}</source>
      <pubDate>{pub_date_rfc822}</pubDate>
      <guid isPermaLink="true">{link}</guid>
    </item>"""
        rss_items.append(item)
    
    # Build complete RSS feed
    rss_feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(feed_title)}</title>
    <link>https://lewdry.github.io/ramah/</link>
    <description>{escape(feed_description)}</description>
    <language>en</language>
    <lastBuildDate>{last_build_date_rfc822}</lastBuildDate>
    <atom:link href="https://lewdry.github.io/ramah/{os.path.basename(xml_file)}" rel="self" type="application/rss+xml"/>
{chr(10).join(rss_items)}
  </channel>
</rss>"""
    
    # Write to file
    with open(xml_file, 'w', encoding='utf-8') as f:
        f.write(rss_feed)
    
    print(f"Generated {xml_file} with {len(stories)} items")

def main():
    # Paths
    data_dir = "docs"
    good_news_json = os.path.join(data_dir, "good_news.json")
    old_news_json = os.path.join(data_dir, "old_news.json")
    good_news_xml = os.path.join(data_dir, "good_news.xml")
    old_news_xml = os.path.join(data_dir, "old_news.xml")
    
    # Generate RSS feeds
    generate_rss_feed(
        good_news_json,
        good_news_xml,
        "Ramah: Good News Feed",
        "Positive news stories from around the world, filtered by sentiment analysis"
    )
    
    generate_rss_feed(
        old_news_json,
        old_news_xml,
        "Ramah: Archived Good News",
        "Archived positive news stories from the Ramah collection"
    )

if __name__ == "__main__":
    main()
