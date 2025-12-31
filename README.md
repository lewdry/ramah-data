# Ramah News Aggregator

Ramah is a 'good news' aggregator that filters news headlines from major sources to find stories with a positive sentiment.

## How it Works

The backend of Ramah is powered by a Python script located at `scripts/fetch_news.py`.

1.  **RSS Fetching**: The script monitors several RSS feeds from BBC News, ABC News (Australia), and The Guardian.
2.  **Sentiment Analysis**: It uses two sentiment analysis tools to ensure high-quality filtering:
    - **VADER**: A dictionary and rule-based sentiment analysis tool.
    - **TextBlob**: A sentiment analysis tool based on NLTK.
    The script calculates the **mean polarity score** from both tools.
3.  **Block List**: Before sentiment analysis, headlines are checked against a block list (e.g., "kill", "bomb", "murder"). If a headline contains any of these words, it is immediately disregarded.
4.  **Filtering**: Only stories with a mean sentiment score above `0.2` are kept.
5.  **Content Extraction**: For positive stories, the script attempts to scrape the first sentence of the article content using `BeautifulSoup`. If scraping fails, it falls back to the RSS summary/description.
6.  **Data Storage**: The filtered "good news" items are stored in `data/good_news.json`. Each item includes `mean_score`, `vader_score`, and `textblob_score` as metadata. To keep the feed fresh, this file is capped at 100 stories. Any stories beyond this limit are automatically moved to `data/old_news.json`.

## Installation & Setup

To run the news fetcher locally, follow these steps:

### Prerequisites
- Python 3.8 or higher.

### Step-by-Step Setup

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/ramah.git
    cd ramah
    ```

2.  **Create a virtual environment**:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    ```

3.  **Install dependencies**:
    ```bash
    pip3 install -r requirements.txt
    ```

4.  **Run the script**:
    ```bash
    python3 scripts/fetch_news.py
    ```

After running, check the `data/good_news.json` file for recent stories, `data/old_news.json` for archived stories, and `data/fetch.log` for execution logs.

## GitHub Actions Scheduling

You can automate the news fetching process by scheduling it to run as a GitHub Action. This ensures your app always has the latest positive news.

### 1. Create the Workflow File
The workflow is already set up at `.github/workflows/fetch_news.yml`. It runs every hour and pushes any updates back to the repository using the official `github-actions[bot]`.

### 2. Permissions Note
Ensure that the GitHub Action has "Read and write permissions" under **Settings > Actions > General > Workflow permissions** so it can commit the updated data file back to your repository.

## Maintenance

If you ever change your `BLOCK_LIST` or `SENTIMENT_THRESHOLD` in `fetch_news.py` and want to apply those changes to your existing data immediately, you can run the cleanup utility:

```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)/scripts
python3 scripts/cleanup_news.py
```

This will scan `data/good_news.json` and remove any stories that no longer meet your criteria.
