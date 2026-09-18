import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests


SITE_URL = "https://yusuke8696.github.io/"
MAPPING_FILE = Path("blogger-pages.json")

CLIENT_ID = os.environ["BLOGGER_CLIENT_ID"]
CLIENT_SECRET = os.environ["BLOGGER_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["BLOGGER_REFRESH_TOKEN"]
BLOG_ID = os.environ["BLOGGER_BLOG_ID"]


def get_access_token():
    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "refresh_token": REFRESH_TOKEN,
            "grant_type": "refresh_token",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def load_mapping():
    if not MAPPING_FILE.exists():
        return {}

    with MAPPING_FILE.open(encoding="utf-8") as f:
        return json.load(f)


def save_mapping(mapping):
    with MAPPING_FILE.open("w", encoding="utf-8") as f:
        json.dump(
            mapping,
            f,
            ensure_ascii=False,
            indent=2,
        )
        f.write("\n")


def extract_title(html):
    match = re.search(
        r"<title[^>]*>(.*?)</title>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return "AI・PC活用ブログ"

    title = re.sub(r"<[^>]+>", "", match.group(1))
    return title.strip()


def extract_body(html):
    match = re.search(
        r"<body[^>]*>(.*?)</body>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not match:
        raise RuntimeError("<body> が見つかりません。")

    return match.group(1).strip()


def extract_styles(html):
    styles = re.findall(
        r"<style[^>]*>(.*?)</style>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not styles:
        return ""

    return "<style>\n" + "\n".join(styles) + "\n</style>\n"


def absolutize_urls(content):
    def replace_attr(match):
        attribute = match.group(1)
        quote = match.group(2)
        value = match.group(3)

        # 変更しないURL
        if (
            value.startswith(("http://", "https://", "//"))
            or value.startswith(("#", "mailto:", "tel:", "javascript:", "data:"))
        ):
            return match.group(0)

        absolute = urljoin(SITE_URL, value)

        return f"{attribute}={quote}{absolute}{quote}"

    return re.sub(
        r"""(href|src)\s*=\s*(["'])(.*?)\2""",
        replace_attr,
        content,
        flags=re.IGNORECASE,
    )


def prepare_content(html):
    styles = extract_styles(html)
    body = extract_body(html)

    content = styles + body
    content = absolutize_urls(content)

    return f"""
<div class="github-home">
{content}
</div>
""".strip()


def create_page(access_token, title, content):
    url = (
        f"https://www.googleapis.com/blogger/v3/"
        f"blogs/{BLOG_ID}/pages/"
    )

    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        params={
            "isDraft": "false",
        },
        json={
            "title": title,
            "content": content,
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def update_page(access_token, page_id, title, content):
    url = (
        f"https://www.googleapis.com/blogger/v3/"
        f"blogs/{BLOG_ID}/pages/{page_id}"
    )

    response = requests.put(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json={
            "id": page_id,
            "blog": {
                "id": BLOG_ID,
            },
            "title": title,
            "content": content,
        },
        timeout=30,
    )

    response.raise_for_status()
    return response.json()


def main():
    html_path = Path(
        sys.argv[1] if len(sys.argv) > 1 else "_site/index.html"
    )

    if not html_path.exists():
        raise FileNotFoundError(
            f"{html_path} が見つかりません。"
            "Jekyllを先にビルドしてください。"
        )

    html = html_path.read_text(encoding="utf-8")

    title = extract_title(html)
    content = prepare_content(html)

    mapping = load_mapping()
    page_id = mapping.get("index.html")

    access_token = get_access_token()

    if page_id:
        print(f"Updating Blogger page: {page_id}")

        try:
            result = update_page(
                access_token,
                page_id,
                title,
                content,
            )

        except requests.HTTPError as e:
            # Blogger側で手動削除された場合は作り直す
            if e.response is not None and e.response.status_code == 404:
                print(
                    "Mapped Blogger page was not found. "
                    "Creating a new page."
                )

                result = create_page(
                    access_token,
                    title,
                    content,
                )

                mapping["index.html"] = result["id"]
                save_mapping(mapping)

            else:
                raise

    else:
        print("Creating Blogger home page.")

        result = create_page(
            access_token,
            title,
            content,
        )

        mapping["index.html"] = result["id"]
        save_mapping(mapping)

    print(f"Blogger Page ID: {result['id']}")
    print(f"Blogger Page URL: {result.get('url', '(unknown)')}")


if __name__ == "__main__":
    main()
