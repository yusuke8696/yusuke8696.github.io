"""Sync the rendered home page; credentials and HTTP helpers match Posts."""

import argparse
import html as html_module
import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode

from sync_blogger import (
    SITE_BASE_URL, convert_relative_urls, get_access_token,
    load_mapping, request, save_mapping,
)

MAPPING_FILE = "blogger-pages.json"
SOURCE = SITE_BASE_URL + "index.html"


def prepare_page(html):
    if re.search(r"\{%|\{\{", html):
        raise ValueError("Unrendered Liquid: build Jekyll and use _site/index.html")
    title = re.search(r"<title\b[^>]*>(.*?)</title>", html, re.I | re.S)
    body = re.search(r"<body\b[^>]*>(.*?)</body>", html, re.I | re.S)
    if not title or not title.group(1).strip() or not body or not body.group(1).strip():
        raise ValueError("Rendered page must contain a nonempty title and body")
    head = re.search(r"<head\b[^>]*>(.*?)</head>", html, re.I | re.S)
    styles = re.findall(r"<style\b[^>]*>.*?</style>", head.group(1) if head else "", re.I | re.S)
    content = convert_relative_urls("\n".join(styles) + "\n" + body.group(1), "index.html")
    return html_module.unescape(title.group(1).strip()), (
        f'<div class="github-home" data-blogger-source="{SOURCE}">\n{content}\n</div>'
    )


class SourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.matches = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        # Recognize pages created by the old script as well as the new marker.
        if attrs.get("data-blogger-source") == SOURCE or (
            tag == "div" and "github-home" in (attrs.get("class") or "").split()
        ):
            self.matches = True


def find_existing_page(blog_id, token):
    matches = set()
    for status in ("live", "draft", "imported"):
        query = urlencode({"view": "ADMIN", "fetchBodies": "true", "status": status})
        result = request(
            f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/pages?{query}",
            headers={"Authorization": f"Bearer {token}"},
        )
        for page in result.get("items", []):
            parser = SourceParser()
            parser.feed(page.get("content", ""))
            if parser.matches:
                matches.add(str(page["id"]))
    if len(matches) > 1:
        raise RuntimeError("Multiple home pages found; select the intended ID in blogger-pages.json")
    return next(iter(matches), None)


def write_page(blog_id, token, title, content, page_id=None):
    endpoint = f"https://www.googleapis.com/blogger/v3/blogs/{blog_id}/pages"
    return request(
        endpoint + (f"/{page_id}" if page_id else ""),
        data=json.dumps({"title": title, "content": content}).encode("utf-8"),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        method="PUT" if page_id else "POST",
    )


def sync_page(html_path, mapping_file=MAPPING_FILE):
    title, content = prepare_page(Path(html_path).read_text(encoding="utf-8"))
    mapping = load_mapping(mapping_file)
    if not isinstance(mapping, dict) or any(
        not isinstance(value, str) or not value.isdigit() for value in mapping.values()
    ):
        raise ValueError("Page mapping must be an object of path: numeric ID strings")
    token = get_access_token()
    blog_id = os.environ["BLOGGER_BLOG_ID"]
    page_id = mapping.get("index.html")
    if not page_id:
        page_id = find_existing_page(blog_id, token)
        if page_id:
            mapping["index.html"] = page_id
            save_mapping(mapping_file, mapping)
    # Fail on 404/auth/network errors: never silently replace a mapped Page.
    # Inserts are not retried. A later run recovers their source marker.
    result = write_page(blog_id, token, title, content, page_id)
    result_id = str(result["id"])
    if not result_id.isdigit() or (page_id and page_id != result_id):
        raise RuntimeError("Blogger returned an unexpected Page ID")
    if mapping.get("index.html") != result_id:
        mapping["index.html"] = result_id
        save_mapping(mapping_file, mapping)
    print(f"Blogger Page ID: {result_id}")
    print(f"Blogger Page URL: {result.get('url', '(unknown)')}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html_path", nargs="?", default="_site/index.html")
    args = parser.parse_args()
    sync_page(args.html_path)


if __name__ == "__main__":
    main()
