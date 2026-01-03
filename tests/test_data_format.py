import json
import importlib.util

spec = importlib.util.spec_from_file_location('fetch_news','scripts/fetch_news.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_load_list_and_save_preserve(tmp_path):
    p = tmp_path / "good_news.json"
    stories = [{'headline':'h','link':'l','timestamp':'2026-01-01T00:00:00Z'}]
    p.write_text(json.dumps(stories, indent=2))

    data = m.load_data(str(p))
    assert isinstance(data, list) and data == stories

    # Saving without last_run should preserve legacy list format
    m.save_data(data, str(p))
    loaded = json.loads(p.read_text())
    assert isinstance(loaded, list)
    assert loaded == stories


def test_save_with_last_run_writes_wrapped(tmp_path):
    p = tmp_path / "good_news.json"
    stories = [{'headline':'h2','link':'l2','timestamp':'2026-01-02T00:00:00Z'}]
    p.write_text(json.dumps(stories, indent=2))

    last_run = "2026-01-03T12:00:00Z"
    m.save_data(stories, str(p), last_run=last_run)

    content = json.loads(p.read_text())
    assert isinstance(content, dict)
    assert content['last run'] == last_run
    assert content['stories'] == stories


def test_load_wrapped_format(tmp_path):
    p = tmp_path / "good_news.json"
    stories = [{'headline':'h3','link':'l3'}]
    wrapped = {'last run': '2026-01-01T00:00:00Z', 'stories': stories}
    p.write_text(json.dumps(wrapped, indent=2))

    data = m.load_data(str(p))
    assert data == stories


def test_normalize_preserves_last_run(tmp_path):
    p = tmp_path / "good_news.json"
    stories = [{'headline':'h','link':'https://www.bbc.co.uk/news/1', 'source':'Bad', 'timestamp':'2026-01-01T00:00:00Z'}]
    wrapped = {'last run': '2026-01-01T00:00:00Z', 'stories': stories}
    p.write_text(json.dumps(wrapped, indent=2))

    # Import normalize_sources and point it at this file
    spec_ns = importlib.util.spec_from_file_location('normalize_sources','scripts/normalize_sources.py')
    ns = importlib.util.module_from_spec(spec_ns)
    spec_ns.loader.exec_module(ns)
    ns.DATA_FILE = str(p)
    ns.main()

    content = json.loads(p.read_text())
    assert 'last run' in content
    assert content['last run'] == wrapped['last run']
    assert content['stories'][0]['source'] == 'BBC News'
