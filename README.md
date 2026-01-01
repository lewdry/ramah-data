# Ramah-Data: News Aggregator

This repository fetches, filters and publishes curated 'good news' as static JSON, intended for consumption by frontend clients.

The JSON is published via GitHub Pages.

```
██████╗  █████╗ ███╗   ███╗ █████╗ ██╗  ██╗
██╔══██╗██╔══██╗████╗ ████║██╔══██╗██║  ██║
██████╔╝███████║██╔████╔██║███████║███████║
██╔══██╗██╔══██║██║╚██╔╝██║██╔══██║██╔══██║
██║  ██║██║  ██║██║ ╚═╝ ██║██║  ██║██║  ██║
╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝
```

## How it Works

The backend of Ramah is powered by a Python script located at `scripts/fetch_news.py`.

1.  **RSS Fetching**: The script monitors several RSS feeds from BBC News, ABC News (Australia), The Guardian, SBS News, Ars Technica, AP News, NPR News.
2.  **Sentiment Analysis**: It uses two sentiment analysis tools to ensure high-quality filtering:
    - **VADER**: A dictionary and rule-based sentiment analysis tool.
    - **TextBlob**: A sentiment analysis tool based on NLTK.
    The script calculates the **mean polarity score** from both tools.
3.  **Block List**: Before sentiment analysis, headlines are checked against a block list (e.g., "kill", "bomb", "murder" etc.). If a headline contains any of these words, it is immediately disregarded.
4.  **Filtering**: Only stories with a mean sentiment score above `0.5` (on a scale of -1 to +1) are kept.
5.  **Content Extraction**: For positive stories, the script attempts to pull the first sentence of the article content using `BeautifulSoup`. If scraping fails, it falls back to the RSS summary/description.
6.  **Data Storage**: The filtered "good news" items are stored in `docs/good_news.json`. Each item includes `mean_score`, `vader_score`, and `textblob_score` as metadata. To keep the feed fresh, this file is capped at 250 stories. Any stories beyond this limit are automatically moved to `docs/old_news.json`.

## Included RSS Feeds

The fetcher monitors a curated list of feeds from a small set of publishers. Current active feeds include:

- **BBC News**: Top Stories, World, UK, Business, Technology, Science & Environment, Health, Entertainment & Arts
- **ABC News (Australia)**: Top Stories, National
- **The Guardian**: World, Australia, Environment, Science, Technology, Lifestyle
- **SBS News**: Top Stories
- **Ars Technica**: Technology, Science, Tech Policy, Gaming
- **AP News**: Top News
- **NPR**: Top Stories, World, Politics, Business, Technology, Science, Health

Note: Some previously configured sub-feeds (several ABC sub-feeds, a Guardian politics feed, a few SBS sub-feeds, and multiple AP sub-feeds) were returning 404/500 errors and have been pruned to keep the job reliable. If you want specific sub-feeds re-added, I can search for updated endpoints and add them.

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

After running, check the `docs/good_news.json` file for recent stories, `docs/old_news.json` for archived stories, and `docs/fetch.log` for execution logs. If you want to migrate existing files from `data/` to `docs/`, run: `mkdir -p docs && git mv data/* docs/ && git commit -m "Move data -> docs"`.

## GitHub Actions Scheduling

Automate the news fetching process by scheduling it to run as a GitHub Action. This ensures the app always has the latest positive news.

### 1. Create the Workflow File

### 2. Permissions Note
Ensure that the GitHub Action has "Read and write permissions" under **Settings > Actions > General > Workflow permissions** so it can commit the updated files in `docs/` back to your repository.

## Maintenance

If you ever change your `BLOCK_LIST`, `SENTIMENT_THRESHOLD`, or other filtering behavior in `fetch_news.py` and want to apply those changes to your existing data immediately, you can run the cleanup utility:

```bash
# (run from repository root)
export PYTHONPATH=$PYTHONPATH:$(pwd)/scripts
python3 scripts/cleanup_news.py
```

This will scan `docs/good_news.json` and remove any stories that no longer meet your criteria.

### Source normalization & canonical mapping 🔧

To keep publisher names consistent, the project maintains a canonical source mapping in `scripts/fetch_news.py`:

- `SOURCE_MAP` is a dictionary mapping identifying substrings (usually parts of a feed URL or link) to canonical publisher names (e.g., `'abc.net.au': 'ABC News'`).
- The helper `canonical_source(feed_url, feed_title=None, link=None)` chooses the canonical name when ingesting feeds.

If you add or update mappings in `SOURCE_MAP`, apply the canonical names to existing saved items by running:

```bash
python3 scripts/normalize_sources.py
```

This script updates `docs/good_news.json` in-place, replacing ambiguous or inconsistent `source` values with their canonical names.

### Automation (GitHub Actions) ⚙️

The repository includes a scheduled GitHub Actions workflow (`.github/workflows/fetch_news.yml`) that runs hourly. The workflow now:

1. Runs `scripts/fetch_news.py` to fetch and ingest new stories.
2. Runs `scripts/cleanup_news.py` to remove stories that no longer meet the latest filters.
3. Runs `scripts/normalize_sources.py` to ensure `source` fields are canonical.
4. Commits and pushes any changes in `docs/` back to the repository.

This keeps the data fresh and consistent without manual intervention.
