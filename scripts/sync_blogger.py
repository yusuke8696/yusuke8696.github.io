import json
import os
import sys
import urllib.parse
import urllib.request
from html.parser import HTMLParser


class ArticleParser(HTMLParser):
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
                f' {k}="{v}"' if v is not None else f" {k}"
                for k, v in attrs
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


def request(url, data=None, headers=None, method=None):
    req = urllib.request.Request(
        url,
        data=data,
        headers=headers or {},
        method=method,
    )
    with urllib.request.urlopen(req) as res:
        return json.loads(res.read())


def get_access_token():
    data = urllib.parse.urlencode({
        "client_id": os.environ["BLOGGER_CLIENT_ID"],
        "client_secret": os.environ["BLOGGER_CLIENT_SECRET"],
        "refresh_token": os.environ["BLOGGER_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()

    result = request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    return result["access_token"]


def main():
    article_path = sys.argv[1]

    with open(article_path, encoding="utf-8") as f:
        html = f.read()

    parser = ArticleParser()
    parser.feed(html)

    if not parser.title:
        raise RuntimeError("titleが見つかりません")

    if not parser.content:
        raise RuntimeError("article要素が見つかりません")

    body = {
        "title": parser.title.strip(),
        "content": "".join(parser.content),
    }

    token = get_access_token()
    blog_id = os.environ["BLOGGER_BLOG_ID"]

    result = request(
        f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/posts?isDraft=true",
        data=json.dumps(body).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    print("Created:", result["title"])
    print("Post ID:", result["id"])


if __name__ == "__main__":
    main()
