# yusuke8696.github.io

## サイトマップ

### jekyll-sitemap による自動生成

`_config.yml` で `jekyll-sitemap` を有効にし、GitHub PagesのJekyllビルド時にサイトマップを自動生成します。

公開URL：

`https://yusuke8696.github.io/sitemap.xml`

サイトマップには、トップページと `articles/` 配下の公開HTMLが含まれます。

記事を追加した際に `sitemap.xml` を手動で編集する必要はありません。GitHub Pagesのビルド時に自動生成されます。

`robots.txt` からも以下のサイトマップを参照します。

`Sitemap: https://yusuke8696.github.io/sitemap.xml`

Google Search ConsoleやBing Webmaster Toolsには、リポジトリ内のファイルではなく、公開された `sitemap.xml` のURLを登録してください。

所有権確認用のファイルは引き続き公開しますが、サイトマップには含めません。

GitHub PagesのJekyllビルドを使用するため、`.nojekyll` は追加しないでください。

参考: [jekyll-sitemap公式](https://github.com/jekyll/jekyll-sitemap)

### サイトマップのCI検証

PRおよび `main` へのpush時に `Check sitemaps` Workflowを実行します。

GitHub Pagesと同等のJekyllビルドを行い、主に以下を確認します。

- `sitemap.xml` が正常なXMLとして生成されること
- トップページがサイトマップに含まれること
- `articles/` 配下の記事がサイトマップに含まれること
- URLが重複していないこと
- `robots.txt` が `/sitemap.xml` を参照していること
- Search Console / Bingの所有権確認ファイルが保持されていること

## 記事一覧の自動更新

`main` へのマージとGitHub Pagesのビルドで、トップページの新着6件（公開日の降順）と全記事一覧に自動反映します。

JavaScript不要のHTMLリンクなので、検索エンジンはトップページから各記事を辿ることができます。ただし、検索エンジンによるインデックス登録の時期や実施を保証するものではありません。

`articles/` 配下のHTMLの先頭に以下のFront Matterを記載し、その後にHTML本文を配置してください。

```yaml
---
layout: null
title: "記事タイトル"
description: "記事の概要"
published_date: "2026-09-19"
---
```

`published_date` には実際の公開日を指定します。記事URLは変わりません。

Front MatterがないHTMLも、ファイル名を表示名として全記事一覧に掲載します。新着欄でタイトルや概要を表示する場合は、上記の情報を設定してください。

全記事一覧は現在、トップページ内に全件掲載します。
