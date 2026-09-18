# yusuke8696.github.io

## 検索エンジン別サイトマップ

### jekyll-sitemap による自動生成

`_config.yml` で `jekyll-sitemap` を有効にし、GitHub Pagesのビルド時に `https://yusuke8696.github.io/sitemaps/sitemap.xml` を生成します。手書きの同名ファイルは生成を妨げるため削除しました。公開先は `_config.yml` の `permalink` で `/sitemaps/sitemap.xml` に変更し、ルートの `sitemap.xml` は生成しません。`robots.txt` も新しいURLを参照します。フォルダ配下からサイト全体のURLを通知するため、ルートサイトのSearch ConsoleプロパティでこのURLを直接送信し、プラグイン方式で取得できるか確認してください。取得成功や順位改善を保証する変更ではありません。

トップページと `articles/` 配下の公開HTMLが対象です。記事追加時に標準 `sitemap.xml` のURL一覧を手で編集する必要はありません。所有権確認ファイルは引き続き公開しますが、サイトマップには含めません。`.nojekyll` は追加しないでください。

参考: [jekyll-sitemap公式](https://github.com/jekyll/jekyll-sitemap)

### 既存のGoogle用・Bing用

GitHub Pagesの標準Jekyllビルドで次の2ファイルを自動生成します。

- Google Search Console: `https://yusuke8696.github.io/sitemap_google.xml`
- Bing Webmaster Tools: `https://yusuke8696.github.io/sitemap_bing.xml`

どちらもUTF-8の標準XMLサイトマップです。Google版は `url` 内に `loc` と `lastmod` をそれぞれ改行して記載します。Bing版は従来と同じXML構造を使います。この2ファイルも比較用に残します。

Google版は `_includes/google-sitemap.xml`、Bing版は `_includes/search-sitemap.xml` を使用し、トップページと `articles/` 以下のHTMLを自動収集します。記事PRが下書きの間は本番に出ず、mainへのマージとPagesビルド後に反映されます。

Google版の更新日は `_data/sitemap_dates.json` で管理します。HTMLを追加・変更してコミットした後、`python .github/scripts/update-sitemap-dates.py` を実行し、更新されたJSONも同じPRへコミットしてください。Gitの最終変更コミット日を使い、ビルド日で一律更新しません。内容変更を伴わない整形等のコミットでは、必要に応じて実際の内容更新日に修正してください。新記事の日付が欠ける場合はCIが失敗するため、マージ前に補完します。

ソースのXMLにはJekyllのfront matterとLiquidが含まれます。Search Console等にはGitHubのソースURLではなく、上記の公開URLを登録してください。PagesのSourceが「Deploy from a branch」でJekyllを使う標準構成が前提です。`.nojekyll` を追加したり、未ビルドのソースをそのまま配信する設定にすると動作しません。

PRの `Check sitemaps` は実際のPages用Jekyllビルドと3種類のXML解析、記事網羅性、所有権確認ファイルの保持を検証します。

既存XMLもGoogleの対応形式です。URLを分けるだけでGoogleの取得エラーが解消する保証はありません。

参考: [Google公式の対応サイトマップ形式](https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap?hl=ja)

## 記事一覧の自動更新

mainへのマージとPagesビルドで、トップページの新着6件（公開日の降順）と全記事一覧に自動反映します。JavaScript不要のHTMLリンクなので、Googleはトップページから記事を辿れます。インデックス登録の時期・実施を保証する機能ではありません。

`articles/` 配下のHTMLの先頭に次を記載し、その後に既存と同様のHTML本文を置いてください。公開日は実際の日付を指定します。記事URLは変わりません。

```yaml
---
layout: null
title: "記事タイトル"
description: "記事の概要"
published_date: "2026-09-19"
---
```

この情報がないHTMLも、ファイル名を表示名として全記事一覧に掲載します。新着欄でタイトルや概要を表示する場合は上記情報を付けてください。全記事一覧は現在トップページ内に全件掲載します。
