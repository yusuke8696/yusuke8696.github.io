import json
import os
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser


class ArticleParser(HTMLParser):
    """GitHub PagesのHTMLからtitleとarticle本文を抽出する。"""

    def __init__(self):
        super().__init__()
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

            attr_text = "".join(
                f' {key}="{value}"' if value is not None else f" {key}"
                for key, value in attrs
            )

            self.content.append(f"<{tag}{attr_text}>")

    def handle_startendtag(self, tag, attrs):
        if self.in_article:
            attr_text = "".join(
                f' {key}="{value}"' if value is not None else f" {key}"
                for key, value in attrs
            )

            self.content.append(f"<{tag}{attr_text}>")

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False

        if self.in_article:
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


def request(url, data=None, headers=None, method=None):
    """HTTPリクエストを送信してJSONを返す。"""

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
        error_body = e.read().decode("utf-8")

        print("Blogger API error:")
        print(error_body)

        raise


def get_access_token():
    """Refresh TokenからAccess Tokenを取得する。"""

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

    if "access_token" not in result:
        raise RuntimeError("Access Tokenを取得できませんでした。")

    return result["access_token"]


def load_mapping(mapping_file):
    """GitHub記事とBlogger Post IDの対応表を読み込む。"""

    if not os.path.exists(mapping_file):
        return {}

    with open(mapping_file, encoding="utf-8") as f:
        return json.load(f)


def save_mapping(mapping_file, mapping):
    """対応表を保存する。"""

    with open(mapping_file, "w", encoding="utf-8") as f:
        json.dump(
            mapping,
            f,
            ensure_ascii=False,
            indent=2,
        )

        f.write("\n")


def parse_article(article_path):
    """HTMLファイルからタイトルと本文を取得する。"""

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


def create_post(blog_id, token, title, content):
    """Bloggerに新しい下書きを作成する。"""

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
    """既存のBlogger記事を更新する。"""

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

    # HTML解析
    title, content = parse_article(article_path)

    print(f"Article: {article_path}")
    print(f"Title: {title}")

    # Blogger認証
    token = get_access_token()
    blog_id = os.environ["BLOGGER_BLOG_ID"]

    # Post ID対応表
    mapping = load_mapping(mapping_file)

    if article_path in mapping:
        # -------------------------
        # 既存記事
        # -------------------------

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
        # -------------------------
        # 新規記事
        # -------------------------

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
