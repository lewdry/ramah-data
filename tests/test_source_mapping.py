import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location('fetch_news','scripts/fetch_news.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_abc():
    assert m.canonical_source('https://www.abc.net.au/news/feed/45910/rss.xml', 'Top Stories', 'https://www.abc.net.au/news/1') == 'ABC News'


def test_bbc_strip():
    assert m.canonical_source('https://feeds.bbci.co.uk/news/rss.xml', 'BBC News - Top Stories', 'https://www.bbc.co.uk/news/1') == 'BBC News'


def test_arstechnica():
    assert m.canonical_source('https://feeds.arstechnica.com/arstechnica/index', 'Ars Technica - All content', 'https://arstechnica.com/article') == 'Ars Technica'


def test_guardian_link():
    assert m.canonical_source('https://unknown/feed', 'Top Stories', 'https://www.theguardian.com/world/1') == 'The Guardian'


if __name__ == '__main__':
    test_abc()
    test_bbc_strip()
    test_arstechnica()
    test_guardian_link()
    print('All source mapping tests passed.')
