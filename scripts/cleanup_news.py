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
        
        # 1. Block list check
        is_blocked = any(blocked_word.lower() in headline.lower() for blocked_word in fetch_news.BLOCK_LIST)
        
        # 2. Score threshold check
        is_below_threshold = mean_score <= fetch_news.SENTIMENT_THRESHOLD
        
        if is_blocked or is_below_threshold:
            print(f"Removing: {headline[:50]}... (Blocked: {is_blocked}, Score: {mean_score})")
            removed_count += 1
            continue
            
        cleaned_data.append(item)
        
    if removed_count > 0:
        with open(fetch_news.DATA_FILE, 'w') as f:
            json.dump(cleaned_data, f, indent=2)
        print(f"Successfully removed {removed_count} out of {initial_count} items.")
    else:
        print("No items removed.")

if __name__ == "__main__":
    cleanup()
