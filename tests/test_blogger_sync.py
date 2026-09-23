import contextlib
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import sync_blogger as posts
import sync_blogger_page as pages

HTML = '<html><head><title>Home &amp; AI</title><style>a {color:red}</style></head><body><a href="articles/a.html">A</a><a href="#all">All</a><img src="assets/a.png"></body></html>'


class PageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.html = Path(self.temp.name) / "index.html"
        self.html.write_text(HTML, encoding="utf-8")
        self.mapping = Path(self.temp.name) / "blogger-pages.json"
        self.addCleanup(patch.stopall)
        patch.dict(os.environ, {"BLOGGER_BLOG_ID": "123"}).start()
        patch.object(pages, "get_access_token", return_value="fake-token").start()
        self.api = patch.object(pages, "request").start()

    def sync(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return pages.sync_page(self.html, self.mapping)

    def test_create_then_update_same_id(self):
        self.api.side_effect = [{}, {}, {}, {"id": "456"}, {"id": "456"}]
        self.sync()
        self.assertEqual(json.loads(self.mapping.read_text()), {"index.html": "456"})
        self.html.write_text(HTML.replace("Home", "New Home"), encoding="utf-8")
        self.sync()
        writes = [c for c in self.api.call_args_list if c.kwargs.get("method")]
        self.assertEqual([c.kwargs["method"] for c in writes], ["POST", "PUT"])
        self.assertTrue(writes[1].args[0].endswith("/pages/456"))
        self.assertEqual(json.loads(writes[1].kwargs["data"])["title"], "New Home & AI")

    def test_lost_mapping_recovers_by_marker_or_legacy_wrapper(self):
        for content in (pages.prepare_page(HTML)[1], '<div class="github-home">old</div>'):
            with self.subTest(content=content):
                self.mapping.write_text("{}")
                self.api.reset_mock()
                self.api.side_effect = [{"items": [{"id": "456", "content": content}]}, {}, {}, {"id": "456"}]
                self.sync()
                self.assertEqual(self.api.call_args.kwargs["method"], "PUT")
                self.assertEqual(json.loads(self.mapping.read_text())["index.html"], "456")

    def test_ambiguous_home_pages_fail_without_write(self):
        marker = pages.prepare_page(HTML)[1]
        self.api.side_effect = [{"items": [{"id": "1", "content": marker}, {"id": "2", "content": marker}]}, {}, {}]
        with self.assertRaisesRegex(RuntimeError, "Multiple"):
            self.sync()
        self.assertFalse(self.mapping.exists())
        self.assertTrue(all("method" not in c.kwargs for c in self.api.call_args_list))

    def test_mapped_errors_never_create_replacement(self):
        for code in (401, 403, 404, 429, 500):
            with self.subTest(code=code):
                self.mapping.write_text('{"index.html": "456"}')
                self.api.reset_mock()
                self.api.side_effect = HTTPError("url", code, "failure", {}, None)
                with self.assertRaises(HTTPError):
                    self.sync()
                self.assertEqual(self.api.call_count, 1)
                self.assertEqual(self.api.call_args.kwargs["method"], "PUT")
                self.assertEqual(json.loads(self.mapping.read_text())["index.html"], "456")

    def test_listing_failure_does_not_insert(self):
        self.api.side_effect = TimeoutError("offline")
        with self.assertRaises(TimeoutError):
            self.sync()
        self.assertEqual(self.api.call_count, 1)
        self.assertFalse(self.mapping.exists())

    def test_insert_timeout_is_not_retried(self):
        self.api.side_effect = [{}, {}, {}, TimeoutError("unknown result")]
        with self.assertRaises(TimeoutError):
            self.sync()
        self.assertEqual(self.api.call_count, 4)
        self.assertFalse(self.mapping.exists())

    def test_invalid_mapping_fails_before_api(self):
        for mapping in ('{bad', '[]', '{"index.html": ""}', '{"index.html": 456}'):
            self.mapping.write_text(mapping)
            with self.assertRaises(ValueError):
                self.sync()
        self.api.assert_not_called()

    def test_html_preparation(self):
        title, content = pages.prepare_page(HTML)
        self.assertEqual(title, "Home & AI")
        self.assertIn('<style>a {color:red}</style>', content)
        self.assertIn('href="https://yusuke8696.github.io/articles/a.html"', content)
        self.assertIn('src="https://yusuke8696.github.io/assets/a.png"', content)
        self.assertIn('href="#all"', content)
        self.assertNotIn('<body>', content)
        self.assertIn('data-blogger-source=', content)

    def test_reject_raw_jekyll_or_empty_document(self):
        for value in (HTML.replace("A</a>", "{% include article-list.html %}</a>"), '<body></body>', '<title>X</title>'):
            with self.assertRaises(ValueError):
                pages.prepare_page(value)


class PostRegressionTests(unittest.TestCase):
    def test_existing_api_contract(self):
        with patch.object(posts, "request", return_value={"id": "9"}) as api:
            posts.create_post("123", "fake", "Title", "Body")
            self.assertTrue(api.call_args.args[0].endswith('/posts?isDraft=true'))
            self.assertEqual(api.call_args.kwargs['method'], 'POST')
            posts.update_post("123", "9", "fake", "Title", "Body")
            self.assertTrue(api.call_args.args[0].endswith('/posts/9'))
            self.assertEqual(api.call_args.kwargs['method'], 'PUT')

    def test_existing_article_mapping_updates_without_create(self):
        with tempfile.TemporaryDirectory() as directory:
            original = Path.cwd()
            os.chdir(directory)
            try:
                Path('article.html').write_text('<title>Title</title><article>Body</article>')
                Path('assets').mkdir()
                Path('assets/article.css').write_text('a {color:red}')
                mapping = Path('blogger-posts.json')
                mapping.write_text('{"article.html": "9"}')
                before = mapping.read_bytes()
                with patch.object(sys, 'argv', ['sync_blogger.py', 'article.html']), patch.dict(os.environ, {'BLOGGER_BLOG_ID': '123'}), patch.object(posts, 'get_access_token', return_value='fake'), patch.object(posts, 'create_post') as create, patch.object(posts, 'update_post', return_value={'id': '9', 'title': 'Title'}) as update, contextlib.redirect_stdout(io.StringIO()):
                    posts.main()
                create.assert_not_called()
                self.assertEqual(update.call_args.args[:2], ('123', '9'))
                self.assertEqual(mapping.read_bytes(), before)
            finally:
                os.chdir(original)


if __name__ == '__main__':
    unittest.main()
