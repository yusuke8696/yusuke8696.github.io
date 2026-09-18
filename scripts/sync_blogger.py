import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser


SITE_BASE_URL = "https://yusuke8696.github.io/"
BLOGGER_CSS_FILE = "assets/article.css"

class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.title = ""
        self.in_title = False
        self.in_article = False
        self.article_depth = 0
        self.content = []

    def handle_starttag(self, tag, attrs):
        if tag == "title":
            self.in_title = True

        if tag == "article":
            self.in_article = True
            self.article_depth = 1
            return

        if self.in_article:
            self.article_depth += 1
            self.content.append(self._build_tag(tag, attrs))

    def handle_startendtag(self, tag, attrs):
        if self.in_article:
            self.content.append(self._build_tag(tag, attrs, True))

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

        if not self.in_article:
            return

        if tag == "article" and self.article_depth == 1:
            self.in_article = False
            self.article_depth = 0
            return

        self.content.append(f"</{tag}>")
        self.article_depth -= 1

    def handle_data(self, data):
        if self.in_title:
            self.title += data

        if self.in_article:
            self.content.append(data)

    def handle_entityref(self, name):
        if self.in_article:
            self.content.append(f"&{name};")

    def handle_charref(self, name):
        if self.in_article:
            self.content.append(f"&#{name};")

    def handle_comment(self, data):
        if self.in_article:
            self.content.append(f"<!--{data}-->")

    def _build_tag(self, tag, attrs, self_closing=False):
        attr_text = ""

        for key, value in attrs:
            if value is None:
                attr_text += f" {key}"
            else:
                escaped = (
                    value.replace("&", "&amp;")
                    .replace('"', "&quot;")
                )
                attr_text += f' {key}="{escaped}"'

        ending = " />" if self_closing else ">"

        return f"<{tag}{attr_text}{ending}"


def request(url, data=None, headers=None, method=None):
    req = urllib.request.Request(
        url,
        data=data,
        headers=headers or {},
        method=method,
    )

    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        print("Blogger API error:")
        print(e.read().decode("utf-8"))
        raise


def get_access_token():
    data = urllib.parse.urlencode({
        "client_id": os.environ["BLOGGER_CLIENT_ID"],
        "client_secret": os.environ["BLOGGER_CLIENT_SECRET"],
        "refresh_token": os.environ["BLOGGER_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode("utf-8")

    result = request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    return result["access_token"]


def load_mapping(mapping_file):
    if not os.path.exists(mapping_file):
        return {}

    with open(mapping_file, encoding="utf-8") as f:
        return json.load(f)


def save_mapping(mapping_file, mapping):
    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(
            mapping,
            f,
            ensure_ascii=False,
            indent=2,
        )
        f.write("\n")


def parse_article(article_path):
    with open(article_path, encoding="utf-8") as f:
        html = f.read()

    parser = ArticleParser()
    parser.feed(html)

    title = parser.title.strip()
    content = "".join(parser.content).strip()

    if not title:
        raise RuntimeError(
            f"titleが見つかりません: {article_path}"
        )

    if not content:
        raise RuntimeError(
            f"article要素が見つかりません: {article_path}"
        )

    return title, content


def convert_relative_urls(content, article_path):
    """
    GitHub Pages向け相対URLを絶対URLへ変換する。

    例:
    qwen-install.html
      ↓
    https://yusuke8696.github.io/articles/qwen-install.html
    """

    article_url = urllib.parse.urljoin(
        SITE_BASE_URL,
        article_path,
    )

    class URLConverter(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.output = []

        def handle_starttag(self, tag, attrs):
            self.output.append(
                self._build_tag(tag, attrs)
            )

        def handle_startendtag(self, tag, attrs):
            self.output.append(
                self._build_tag(tag, attrs, True)
            )

        def handle_endtag(self, tag):
            self.output.append(f"</{tag}>")

        def handle_data(self, data):
            self.output.append(data)

        def handle_entityref(self, name):
            self.output.append(f"&{name};")

        def handle_charref(self, name):
            self.output.append(f"&#{name};")

        def handle_comment(self, data):
            self.output.append(f"<!--{data}-->")

        def _build_tag(self, tag, attrs, self_closing=False):
            converted = []

            for key, value in attrs:
                if value is not None and key in ("href", "src"):
                    parsed = urllib.parse.urlparse(value)

                    # http/https/mailto/# などはそのまま
                    if (
                        not parsed.scheme
                        and not value.startswith("//")
                        and not value.startswith("#")
                    ):
                        value = urllib.parse.urljoin(
                            article_url,
                            value,
                        )

                converted.append((key, value))

            attr_text = ""

            for key, value in converted:
                if value is None:
                    attr_text += f" {key}"
                else:
                    escaped = (
                        value.replace("&", "&amp;")
                        .replace('"', "&quot;")
                    )
                    attr_text += f' {key}="{escaped}"'

            ending = " />" if self_closing else ">"

            return f"<{tag}{attr_text}{ending}"

    converter = URLConverter()
    converter.feed(content)

    return "".join(converter.output)


def add_blogger_styles(content):
    with open(BLOGGER_CSS_FILE, encoding="utf-8") as f:
        css = f.read()

    return (
        "<style>\n"
        + css
        + "\n</style>\n"
        + '<div class="blogger-article">\n'
        + content
        + '\n</div>'
    )


def create_post(blog_id, token, title, content):
    body = {
        "title": title,
        "content": content,
    }

    return request(
        (
            "https://www.googleapis.com/blogger/v3/"
            f"blogs/{blog_id}/posts?isDraft=true"
        ),
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )


def update_post(blog_id, post_id, token, title, content):
    body = {
        "title": title,
        "content": content,
    }

    return request(
        (
            "https://www.googleapis.com/blogger/v3/"
            f"blogs/{blog_id}/posts/{post_id}"
        ),
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="PUT",
    )


def main():
    if len(sys.argv) != 2:
        print(
            "Usage: python scripts/sync_blogger.py "
            "articles/example.html"
        )
        sys.exit(1)

    article_path = sys.argv[1]

    if not os.path.exists(article_path):
        raise FileNotFoundError(
            f"記事が存在しません: {article_path}"
        )

    mapping_file = "blogger-posts.json"

    # GitHub Pages HTMLを解析
    title, content = parse_article(article_path)

    # Blogger用に変換
    content = convert_relative_urls(
        content,
        article_path,
    )

    content = add_blogger_styles(content)

    print(f"Article: {article_path}")
    print(f"Title: {title}")

    token = get_access_token()
    blog_id = os.environ["BLOGGER_BLOG_ID"]

    mapping = load_mapping(mapping_file)

    if article_path in mapping:
        post_id = mapping[article_path]

        print(f"Existing Blogger Post ID: {post_id}")
        print("Updating Blogger post...")

        result = update_post(
            blog_id,
            post_id,
            token,
            title,
            content,
        )

        print("Updated successfully.")
        print(f"Title: {result['title']}")
        print(f"Post ID: {result['id']}")

    else:
        print("Creating Blogger draft...")

        result = create_post(
            blog_id,
            token,
            title,
            content,
        )

        post_id = result["id"]

        mapping[article_path] = post_id
        save_mapping(mapping_file, mapping)

        print("Created successfully.")
        print(f"Title: {result['title']}")
        print(f"Post ID: {post_id}")
        print("blogger-posts.json updated.")


if __name__ == "__main__":
    main()
