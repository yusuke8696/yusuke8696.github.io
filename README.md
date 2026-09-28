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

## Blogger Posts / Pages 同期

`Blogger Sync` (`.github/workflows/blogger-sync.yml`) が同期を担当します。
以前の `Blogger Home Sync` は統合済みです。

| 同期元 | Blogger側 | ID対応表 |
| --- | --- | --- |
| `articles/*.html`（サブディレクトリ含む） | Posts（初回は下書き、以降は同じ投稿を更新） | `blogger-posts.json` |
| Jekyllでビルドした `_site/index.html` | Pages（固定ページ） | `blogger-pages.json` |

既存の `scripts/sync_blogger.py` とPost IDは変更していません。
Pagesも同じ標準ライブラリの認証・HTTP・マッピング関数を再利用し、追加のPythonパッケージは不要です。
GitHub Secretsの `BLOGGER_CLIENT_ID`、`BLOGGER_CLIENT_SECRET`、
`BLOGGER_REFRESH_TOKEN`、`BLOGGER_BLOG_ID` を再利用します。
トークンやクライアントシークレットをファイルに記載しないでください。

### 自動・手動実行

mainのindex、記事、includes、data、設定、assets、同期スクリプト・ワークフロー変更で実行します。
index内のLiquidを展開するため、既存サイトマップ検証と同じ
`actions/jekyll-build-pages` でビルドします（Gemfileは不要）。
連続pushでGitHubが待機中の実行をまとめても取りこぼさないよう、
自動実行は最新mainの全記事とホームを同期します。記事数に比例してAPI呼び出しが増えます。
Pages同期が失敗してもPosts同期は実行し、ワークフロー全体は失敗を報告します。

Actions → Blogger Sync → Run workflowでmainを選び、
`target=pages` ならホームだけ、`posts` なら記事だけ、`all` なら両方を同期できます。
`article` を指定すると対象記事を限定できます（pages選択時は無視）。
初回のPages同期は `target=pages` で実行できます。

### ID保存と重複防止

Pagesの対応表は `{"index.html": "Blogger Page ID"}` です。初回作成の戻り値を保存し、
次回以降はそのIDにPUTします。初期値の `{}` を実行前に変更する必要はありません。
PostsとPagesを同一ワークフローで直列化し、途中失敗時にも両対応表の変更をcommitします。
通常のmain更新と競合した場合はrebaseしてpushを再試行し、失敗時には対応表をartifactにも保存します。
mainへのActionsの書き込みをブランチ保護が禁止している場合は、保存ステップが失敗します。

Page作成後にID保存だけ失敗した場合は、次回にBlogger側の本文の
`data-blogger-source` を検索してIDを復旧します。旧スクリプトの `github-home` ラッパーも認識します。
候補が複数なら停止するので、正しいIDを対応表へ設定してください。
同名タイトルだけで他のページを上書きすることはありません。
対応表にあるIDが404を返した場合や認証・通信エラー時は、自動再作成しません。
手動削除後に再作成したい場合は対象IDを確認してから対応表の `index.html` エントリを削除してください。
外部からの同時作成やBloggerの読み取り反映遅延まで含めた厳密な一度限りの作成は保証できません。

### テスト

秘密情報やBloggerへのアクセスなしで実行できます。

```sh
python -m unittest discover -s tests -v
```

作成→同一ID更新、対応表紛失時の復旧、重複候補、API失敗、相対URL変換、
未ビルドLiquidの拒否、既存Postsの更新を検証します。
PRの `Test Blogger Sync` はJekyllビルド後のHTML変換も検証します。

実環境では `target=pages` を2回実行し、ログのPage IDと `blogger-pages.json` が同じこと、
Bloggerのページ数が増えないことを確認してください。indexの文章変更後も同じIDで内容が更新されます。
API実行はこの手動テストおよびmainでの自動実行時に行われます。

同期先は独立URLの固定ページです。BloggerのトップURLやテーマは変更しません。
リンクはGitHub Pagesの絶対URLへ変換し、indexのCSSを保持します。
BloggerテーマとCSSが干渉する可能性があるため、公開ページの見た目は実環境で確認してください。

API仕様: [Pages](https://developers.google.com/blogger/docs/3.0/reference/pages)、
[Pages list](https://developers.google.com/blogger/docs/3.0/reference/pages/list)。
