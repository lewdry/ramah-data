import json
import os
import fetch_news

def cleanup():
    print(f"Loading {fetch_news.DATA_FILE}...")
    if not os.path.exists(fetch_news.DATA_FILE):
        print("Data file not found.")
        return
        
    with open(fetch_news.DATA_FILE, 'r') as f:
        data = json.load(f)
        
    initial_count = len(data)
    cleaned_data = []
    removed_count = 0
    
    for item in data:
        headline = item.get('headline', '')
        mean_score = item.get('mean_score', 0)
        link = item.get('link', '')
        
        # 1. Block list check (headline words)
        is_blocked = any(blocked_word.lower() in headline.lower() for blocked_word in fetch_news.BLOCK_LIST)
        
        # 2. Score threshold check
        is_below_threshold = mean_score <= fetch_news.SENTIMENT_THRESHOLD

        # 3. URL blocklist check (link substrings)
        is_url_blocked = bool(link and any(block in link for block in getattr(fetch_news, 'URL_BLOCKLIST', [])))
        
        if is_blocked or is_below_threshold or is_url_blocked:
            print(f"Removing: {headline[:50]}... (Blocked: {is_blocked}, URL Blocked: {is_url_blocked}, Score: {mean_score})")
            removed_count += 1
            continue
            
        cleaned_data.append(item) 
        
    if removed_count > 0:
        with open(fetch_news.DATA_FILE, 'w') as f:
            json.dump(cleaned_data, f, indent=2)
        print(f"Successfully removed {removed_count} out of {initial_count} items.")

        # Additionally, clean the archive file of any URL-blocked links
        if hasattr(fetch_news, 'ARCHIVE_FILE') and os.path.exists(fetch_news.ARCHIVE_FILE):
            with open(fetch_news.ARCHIVE_FILE, 'r') as f:
                archive = json.load(f)
            archive_initial = len(archive)
            new_archive = []
            removed_archive = 0
            for item in archive:
                link = item.get('link', '')
                if link and any(block in link for block in getattr(fetch_news, 'URL_BLOCKLIST', [])):
                    removed_archive += 1
                    continue
                new_archive.append(item)
            if removed_archive > 0:
                with open(fetch_news.ARCHIVE_FILE, 'w') as f:
                    json.dump(new_archive, f, indent=2)
                print(f"Removed {removed_archive} items from archive ({fetch_news.ARCHIVE_FILE}).")
    else:
        print("No items removed.")

if __name__ == "__main__":
    cleanup()
