import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser


SITE_BASE_URL = "https://yusuke8696.github.io/"


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
    """
    GitHub Pagesの記事デザインのうち、
    Blogger本文で必要なCSSだけを追加する。
    """

    css = """
<style>
.blogger-article {
    color: #202a35;
    font-family: "Noto Sans JP", "Yu Gothic", sans-serif;
    line-height: 1.85;
}

.blogger-article section + section {
    margin-top: 46px;
}

.blogger-article h2 {
    margin: 0 0 22px;
    font-size: 27px;
    line-height: 1.4;
}

.blogger-article h3 {
    margin: 30px 0 10px;
    font-size: 20px;
    line-height: 1.4;
}

.blogger-article p {
    margin: 0 0 18px;
}

.blogger-article a {
    color: #0b756c;
}

.blogger-article .specs {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1px;
    margin: 20px 0 10px;
    overflow: hidden;
    border: 1px solid #dbe3e8;
    background: #dbe3e8;
}

.blogger-article .specs div {
    padding: 13px 16px;
    background: #fbfcfc;
}

.blogger-article .specs dt {
    color: #657382;
    font-size: 13px;
}

.blogger-article .specs dd {
    margin: 2px 0 0;
    font-weight: 700;
}

.blogger-article .flow {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 10px;
    margin: 25px 0;
}

.blogger-article .flow div {
    position: relative;
    padding: 18px 10px;
    color: #07534e;
    background: #e4f3ef;
    border-radius: 7px;
    font-size: 14px;
    font-weight: 700;
    text-align: center;
}

.blogger-article .flow div:not(:last-child)::after {
    position: absolute;
    top: 50%;
    right: -9px;
    color: #0b756c;
    content: ">";
    transform: translateY(-50%);
}

.blogger-article pre {
    overflow-x: auto;
    margin: 18px 0 24px;
    padding: 20px;
    color: #e8f1f0;
    background: #18232b;
    border-radius: 7px;
    font: 14px/1.7 Consolas, "Courier New", monospace;
}

.blogger-article code {
    padding: 2px 5px;
    color: #07534e;
    background: #edf4f2;
    border-radius: 3px;
    font-family: Consolas, "Courier New", monospace;
    font-size: .92em;
}

.blogger-article pre code {
    padding: 0;
    color: inherit;
    background: none;
}

.blogger-article .notice {
    margin: 22px 0;
    padding: 18px 20px;
    background: #fff;
    border: 1px solid #dbe3e8;
    border-left: 4px solid #0b756c;
    border-radius: 0 7px 7px 0;
}

.blogger-article .notice strong {
    color: #07534e;
}

.blogger-article .affiliate-box {
    margin: 26px 0;
    padding: 20px;
    background: #fff8e8;
    border: 1px solid #ead6a4;
    border-radius: 8px;
}

.blogger-article .affiliate-banner-slot {
    margin: 30px 0;
    padding: 20px;
    background: #f6f9fb;
    border: 1px solid #dbe3e8;
    border-radius: 8px;
    text-align: center;
}

.blogger-article .affiliate-banner-slot__label {
    margin: 0 0 14px;
    font-size: 14px;
}

.blogger-article .affiliate-banner-slot__items {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: 16px;
}

.blogger-article .affiliate-banner-slot__ad,
.blogger-article .affiliate-banner-slot__items a {
    line-height: 0;
}

.blogger-article img {
    max-width: 100%;
    height: auto;
}

.blogger-article .next-articles {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    margin-top: 24px;
}

.blogger-article .next-articles a {
    display: block;
    padding: 14px 16px;
    color: #07534e;
    background: #e4f3ef;
    border-radius: 7px;
    font-weight: 700;
    text-decoration: none;
}

.blogger-article ul {
    padding-left: 1.4em;
}

.blogger-article li + li {
    margin-top: 7px;
}

@media (max-width: 640px) {
    .blogger-article .specs,
    .blogger-article .flow {
        grid-template-columns: 1fr;
    }

    .blogger-article .next-articles {
        grid-template-columns: 1fr;
    }

    .blogger-article .flow div:not(:last-child)::after {
        top: auto;
        right: 50%;
        bottom: -14px;
        content: "v";
        transform: translateX(50%);
    }
}
</style>
"""

    return (
        css
        + '\n<div class="blogger-article">\n'
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
