from html.parser import HTMLParser
from pathlib import Path


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs).get('href'))


html = Path('_site/index.html').read_text(encoding='utf-8')
parser = Links()
parser.feed(html)
expected = {'/' + p.as_posix() for p in Path('articles').rglob('*.html')}
assert expected <= set(parser.links), expected - set(parser.links)
assert '{{' not in html and '{%' not in html, 'Unrendered Liquid'
for path in expected:
    output = Path('_site') / path.lstrip('/')
    assert output.exists(), path
    assert not output.read_text(encoding='utf-8').startswith('---'), path
if Path('articles/ci-new-article.html').exists():
    recent = html.split('id="articles"', 1)[1].split('id="all-articles"', 1)[0]
    assert '/articles/ci-new-article.html' in recent
    assert 'CI &amp; 新着記事' in recent
    assert '/articles/ci-plain-article.html' in parser.links
print('All articles are linked in generated HTML and retain their URLs.')
